"""
s_score — Markdown structural (S-score) similarity.

The metric is exposed through a single pair of entry points:

    final_score(text1, text2, fuzzy_th)
    proc(toc1, toc2, toc_dict1, toc_dict2, fuzzy_th)

`final_score` parses both markdown documents and delegates to `proc`.
Both return `(score, debug_info)`.

Background
----------
- ToC extraction: parse heading lines, build a per-document index.
- ToC unification: fuzzy-merge headings across two documents into a shared
  index (rapidfuzz).
- Graph: build a sparse parent→child graph, derive full-descendant graph,
  add forward edges between consecutive nodes to form the "text bush".
- Score: build each document's adjacency bush matrix (edge present) and
  hierarchy bush matrix (edge weighted by |level gap|), diffuse the two into
  one matrix per document with an element-wise max, take the element-wise
  absolute difference of the two documents' merged matrices, and normalise its
  1-norm by the union of both documents' merged structural mass. That union is
  a true upper bound, so the similarity `1 - distance/norm` lies in [0, 1] and
  is symmetric in the two documents.
"""

from collections import defaultdict
import warnings
import re
import sys

import numpy as np
import pandas as pd
from scipy.sparse import lil_matrix, csr_matrix
from rapidfuzz import process as rf_process, fuzz as rf_fuzz
from rapidfuzz.utils import default_process as rf_default_process

# Deeply nested legal documents can require a high recursion limit during
# `disconnected_full_graph` DFS. Set conservatively for the worst observed case.
sys.setrecursionlimit(50000)


# =====================================================================
# 1. ToC extraction
# =====================================================================

def toc_extract(text):
    """Parse `text` into a list of header tuples and a parallel dict.

    Returns:
        headers: list of (line_index, level, title)
        headers_dict: {'loc_index': [...], 'level': [...], 'header': [...]}
    """
    lines = text.strip().split("\n")
    headers = []
    headers_dict = {'loc_index': [], 'level': [], 'header': []}

    for i, line in enumerate(lines):
        match = re.match(r"^(#+)\s+(.*)", line)
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            headers.append((i, level, title))
            headers_dict['loc_index'].append(i)
            headers_dict['level'].append(level)
            headers_dict['header'].append(title)

    return headers, headers_dict


# =====================================================================
# 2. ToC unification
# =====================================================================

# Single source of truth for pairwise heading similarity, shared by the
# structural metric (`toc_fuzzy_unify`) and the heading-F1 metric so both
# score heading matches identically.
HEADING_SCORER = rf_fuzz.WRatio
HEADING_PROCESSOR = rf_default_process


def heading_similarity(a, b):
    """Similarity between two heading strings on the 0–100 rapidfuzz scale.

    Uses the same scorer/processor (`WRatio` + default normalisation) that the
    ToC unifier uses, so the structural and F1 metrics agree on what "matches".
    """
    return HEADING_SCORER(a, b, processor=HEADING_PROCESSOR)


def _normalize_levels(levels):
    """Map raw heading levels to dense, gap-free global levels (per document).

    Two steps in one: (1) shift so the shallowest level becomes 0, then
    (2) reassign so the *distinct levels that actually appear* land on
    consecutive integers, collapsing any gaps. Each distinct level is mapped
    to its rank among the sorted distinct appearing levels.

        appearing 1,2,3,4,5,6  ->  0,1,2,3,4,5   (already consistent, unchanged)
        appearing 1,3,7,8,9    ->  0,1,2,3,4     (gaps collapsed)

    Order is preserved, ties are preserved, so a document keeps its relative
    hierarchy while the scale is made consistent.
    """
    levels = pd.Series(list(levels))
    if len(levels) == 0:
        return levels
    distinct = sorted(set(levels))
    rank = {lvl: i for i, lvl in enumerate(distinct)}
    return levels.map(rank)


def toc_fuzzy_unify(toc_dict1, toc_dict2, threshold):
    """Fuzzy-merge two ToCs onto a shared node index (rapidfuzz)."""
    df1 = pd.DataFrame(toc_dict1)
    df2 = pd.DataFrame(toc_dict2)

    df1['global_level'] = _normalize_levels(df1['level'])

    if len(toc_dict2['level']) > 0:
        df2['global_level'] = _normalize_levels(df2['level'])

    headers2 = list(df2['header']) if len(toc_dict2['level']) > 0 else []

    matches1 = []
    inner_matches = []
    for item in df1['header']:
        ind1 = df1[df1['header'] == item]['loc_index'].values[0]
        if headers2:
            try:
                with warnings.catch_warnings():
                    warnings.filterwarnings('ignore')
                    result = rf_process.extractOne(
                        item, headers2,
                        scorer=HEADING_SCORER,
                        processor=HEADING_PROCESSOR,
                    )
                    match = (result[0], result[1], result[2]) if result else (None, 0, 0)
            except Exception:
                match = (None, 0, 0)
        else:
            match = (None, 0, 0)

        if match[1] > threshold:
            matches1.append((ind1, item, None, match[0], match[1]))
            inner_matches.append((ind1, item, None, match[0], match[1]))
        else:
            matches1.append((ind1, item, None, None, 0))

    matches2 = matches1  # intentional alias (same as reference)
    matches_header2 = [x[1] for x in matches2]

    for item in df2['header']:
        if item not in matches_header2:
            ind2 = df2[df2['header'] == item]['loc_index'].values[0]
            if headers2:
                try:
                    with warnings.catch_warnings():
                        warnings.filterwarnings('ignore')
                        result = rf_process.extractOne(
                            item, list(df1['header']),
                            scorer=HEADING_SCORER,
                            processor=HEADING_PROCESSOR,
                        )
                        match = (result[0], result[1], result[2]) if result else (None, 0, 0)
                except Exception:
                    match = (None, 0, 0)
                if match[1] > threshold:
                    matches2.append((None, match[0], ind2, item, match[1]))
                else:
                    matches2.append((None, None, ind2, item, 0))

    return _finalize_fuzzy_unify(df1, df2, matches2, inner_matches)


def _finalize_fuzzy_unify(df1, df2, matches2, inner_matches):
    """Shared post-processing for fuzzy unification."""
    merged = pd.DataFrame(matches2, columns=['index1', 'header1', 'index2', 'header2', 'score'])
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', FutureWarning)
        merged = merged.fillna(0).infer_objects(copy=False)
    merged['loc_index'] = merged.index1 + merged.index2
    merged = merged.drop(['index1', 'index2'], axis=1)
    merged = merged.sort_values(by='loc_index')
    merged = (merged.reset_index()
                    .reset_index()
                    .drop(['index'], axis=1)
                    .rename(columns={'level_0': 'index'}))

    toc1_index = []
    toc2_index = []

    df1m = df1.merge(merged, left_on='header', right_on='header1', how='inner')
    df1_ar = df1m.to_dict()
    for i in range(len(df1_ar['index'])):
        toc1_index.append((df1_ar['index'][i], df1_ar['global_level'][i], df1_ar['header'][i]))

    if len(matches2) > 0:
        df2m = df2.merge(merged, left_on='header', right_on='header2', how='inner')
        df2_ar = df2m.to_dict()
        for i in range(len(df2_ar['index'])):
            toc2_index.append((df2_ar['index'][i], df2_ar['global_level'][i], df2_ar['header'][i]))

    def _deduplicate(toc_index):
        if not toc_index:
            return []
        df = pd.DataFrame(toc_index)
        d = df.groupby([2, 1])[0].min().reset_index().sort_values(0).to_dict()
        result = [(d[0][i], d[1][i], d[2][i]) for i in range(len(d[0]))]
        result.sort()
        return result

    toc1_index_unique = _deduplicate(toc1_index)
    toc2_index_unique = _deduplicate(toc2_index)

    # After the double reset_index above, `merged` has a clean 0..n-1 RangeIndex,
    # so the node count is simply the row count (0 for an empty frame).
    total_nodes = len(merged)

    toc1_nodes = df1m['level'].count() if len(df1m) > 0 else 0
    con_nodes = pd.DataFrame(inner_matches)[1].count() if inner_matches else 0
    node_recall = con_nodes / toc1_nodes if toc1_nodes > 0 else 0

    return toc1_index_unique, toc2_index_unique, total_nodes, node_recall


# =====================================================================
# 3.a Graph representation
# =====================================================================

def has_cycle(graph):
    """Return True iff `graph` (adjacency dict) contains a directed cycle."""
    visited = set()
    rec_stack = set()

    def is_cyclic(node):
        visited.add(node)
        rec_stack.add(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if is_cyclic(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True
        rec_stack.remove(node)
        return False

    for node in graph:
        if node not in visited:
            if is_cyclic(node):
                return True
    return False


def disconnected_sparse_graph(headers):
    """Parent→direct-children mapping from a `headers` list of (idx, level, title)."""
    graph = defaultdict(list)
    stack = []
    seen_indices = set()

    for line_num, level, _ in headers:
        if line_num in seen_indices:
            continue
        seen_indices.add(line_num)

        while stack and stack[-1][1] >= level:
            stack.pop()
        if stack:
            parent_line, _ = stack[-1]
            graph[parent_line].append(line_num)

        stack.append((line_num, level))

        if line_num not in graph:
            graph[line_num] = []
    return dict(graph)


def disconnected_full_graph(graph):
    """Memoised DFS. Each node's descendant set computed once."""
    memo = {}

    def all_descendants(node):
        if node in memo:
            return memo[node]
        desc = set()
        for child in graph.get(node, []):
            desc.add(child)
            desc |= all_descendants(child)
        memo[node] = desc
        return desc

    return {node: sorted(all_descendants(node)) for node in graph}


def connected_graph(disc_graph, headers):
    """Add forward edges between consecutive header nodes (text bush)."""
    graph = disc_graph.copy()
    for (line_num, _, _), (next_line, _, _) in zip(headers, headers[1:]):
        if next_line > line_num and next_line not in set(disc_graph[line_num]):
            graph[line_num].append(next_line)
    return dict(graph)


# =====================================================================
# 3.b Matrix representation
# =====================================================================

# Adjacency matrix
def graph_to_sparse_matrix(graph, m):
    """Adjacency mapping → sparse m × m CSR matrix."""
    mat = lil_matrix((m, m), dtype=np.float64)
    for i, children in graph.items():
        # mat[i, i] = 1.0 # excluded main diagonal
        for j in children:
            mat[i, j] = 1.0
    return csr_matrix(mat)


# Hierarchical matrix
def levels_vector(toc_index, m):
    """Length-`m` vector of heading levels indexed by node id.

    `toc_index` is a list of (node_id, global_level, title); node ids not present
    in it stay 0. Used to weight bush edges by heading-level gap.
    """
    levels = np.zeros(m)
    for node_id, global_level, _title in toc_index:
        levels[node_id] = global_level
    return levels


def graph_to_level_diff_sparse_matrix(graph, m, levels):
    """Adjacency mapping → sparse m × m CSR matrix weighted by heading-level gap.

    Each edge (i, j) is set to |levels[j] - levels[i]|, the diagonal stays 0.
    `levels` is a sequence of length m indexed by node id.
    """
    mat = lil_matrix((m, m), dtype=np.float64)
    for i, children in graph.items():
        for j in children:
            mat[i, j] = float(abs(levels[j] - levels[i]))
    return csr_matrix(mat)


# =====================================================================
# 4. Structure metric
# =====================================================================

def structure_metric(abs_dist, norm_factor, sim=True):
    """Turn a distance / normaliser pair into the final S-score.

    Normalization method
    --------------------
    This is the **generalized Jaccard (Ruzicka) similarity**. With `abs_dist`
    the cell-wise 1-norm ``Σ|Aij - Bij|`` and `norm_factor` the cell-wise union
    ``Σ max(Aij, Bij)``, the ratio ``abs_dist / norm_factor`` is the Soergel
    distance, and ``1 - abs_dist / norm_factor`` is its complementary similarity
    — i.e. ``Σ min(Aij, Bij) / Σ max(Aij, Bij)`` for non-negative matrices. On
    the binary adjacency channel this reduces to the classic Jaccard index (IoU)
    over graph edges.

    Parameters
    ----------
    abs_dist : float
        Structural distance between the two documents (the 1-norm of their
        matrix difference).
    norm_factor : float
        Upper-bound normaliser (the union of both documents' structural mass).
    sim : bool, default True
        When True, return a similarity in [0, 1]: ``1 - abs_dist / norm_factor``,
        clamped at 0, and 0 when `norm_factor` is 0 (nothing to compare). When
        False, return the raw `abs_dist` unchanged.

    Returns
    -------
    float
        The similarity (`sim=True`) or the raw distance (`sim=False`).
    """
    if sim:
        if norm_factor == 0:
            return 0
        base = 1 - abs_dist / norm_factor
        if base < 0:
            base = 0
    else:
        base = abs_dist
    return base


# =====================================================================
# 5. Additional metrics
# =====================================================================

def toc_coverage(toc1_count, toc2_count):
    """Detection-coverage factor in [0, 1]: 0 when nothing detected, 1 when balanced."""
    total = toc1_count + toc2_count
    if total == 0:
        return 0.0
    return min(1.0, 2 * toc2_count / total)


# =====================================================================
# Public entry points
# =====================================================================

def proc(toc1, toc2, toc_dict1, toc_dict2, fuzzy_th, difs=True, sim=True):
    """Compute the structural similarity (S-score) between two unified ToCs.

    Both documents are fuzzy-unified onto a shared node index, turned into
    "text bush" graphs, and rendered as two per-document matrices: an adjacency
    bush (edge present) and a hierarchy bush (edge weighted by |level gap|).
    The element-wise absolute difference of the documents' matrices gives the
    distance; the element-wise union of their structural mass gives the
    normaliser (a true upper bound). `structure_metric` turns the two into the
    final value.

    Parameters
    ----------
    toc1, toc2 : list
        Header lists from `toc_extract` (output [0]) — used only for the
        coverage diagnostic.
    toc_dict1, toc_dict2 : dict
        ToC dicts from `toc_extract` (output [1]).
    fuzzy_th : float in [0, 100]
        Minimum rapidfuzz WRatio score (0–100) for two headings to be treated
        as the same node. Headings are unified when their match score is
        strictly greater than this cutoff (e.g. 80 ≈ 80% similar).
    difs : bool, default True
        Channel diffusion. When True (default), the adjacency and hierarchy
        channels are fused with an element-wise max (both distance and
        normaliser) so the score reflects both edge presence and level gaps.
        When False, only the adjacency channel is used.
    sim : bool, default True
        When True, return a similarity in [0, 1] (`1 - distance / norm`,
        clamped at 0, symmetric in the two documents). When False, return the
        raw distance instead.

    Returns
    -------
    (graph_similarity, debug_info)
        `graph_similarity` is the score described above; `debug_info` is a dict
        of diagnostics (node counts, distance, normaliser, node recall, ToC
        coverage). On error a `(0, {'error': ...})` pair is returned instead.
    """
    try:

        # Headings fuzzy unification
        toc1_index, toc2_index, total_nodes, node_recall = toc_fuzzy_unify(toc_dict1, toc_dict2, fuzzy_th)

        # Graph definition
        graph1_sparse_d = disconnected_sparse_graph(toc1_index)
        graph2_sparse_d = disconnected_sparse_graph(toc2_index)

        graph1_full_d = disconnected_full_graph(graph1_sparse_d)
        graph2_full_d = disconnected_full_graph(graph2_sparse_d)

        graph1_full = connected_graph(graph1_full_d, toc1_index)
        graph2_full = connected_graph(graph2_full_d, toc2_index)

        if has_cycle(graph1_full):
            graph1_full = graph1_sparse_d
        if has_cycle(graph2_full):
            graph2_full = graph2_sparse_d

        # Node levels (needed by the hierarchy matrix).
        levels1 = levels_vector(toc1_index, total_nodes)
        levels2 = levels_vector(toc2_index, total_nodes)

        # Per-channel bush matrices: adjacency (edge present) and hierarchy
        # (edge weighted by |level gap|).
        adj_mat1 = graph_to_sparse_matrix(graph1_full, total_nodes)
        adj_mat2 = graph_to_sparse_matrix(graph2_full, total_nodes)
        hier_mat1 = graph_to_level_diff_sparse_matrix(graph1_full, total_nodes, levels1)
        hier_mat2 = graph_to_level_diff_sparse_matrix(graph2_full, total_nodes, levels2)

        # Per-cell absolute differences, kept sparse.
        adj_diff = abs(adj_mat1 - adj_mat2)
        hier_diff = abs(hier_mat1 - hier_mat2)

        # Diffusion (if enabled). `merged_norm` is the cell-wise union Σmax(...);
        # dividing the diff by its sum yields the generalized Jaccard (Ruzicka)
        # similarity in `structure_metric`.
        if difs:
            merged_diff = adj_diff.maximum(hier_diff)  # Distance matrix
            merged_norm = adj_mat1.maximum(hier_mat1).maximum(adj_mat2).maximum(hier_mat2)  # Normalization matrix
        else:
            merged_diff = adj_diff
            merged_norm = adj_mat1.maximum(adj_mat2)

        # Distance
        merged_num = float(merged_diff.sum())
        merged_denum = float(merged_norm.sum())

        graph_sim = structure_metric(merged_num, merged_denum, sim=sim)

        debug_info = {
            'total_nodes': total_nodes,
            'distance': merged_num,
            'norm_factor': merged_denum,
            'node_recall': node_recall,
            'toc_coverage': toc_coverage(len(toc1), len(toc2)),
        }
        return graph_sim, debug_info

    except ValueError as e:
        return 0, {'error': str(e)}
    except RecursionError:
        return 0, {'error': 'recursion_depth_exceeded'}
    except Exception as e:
        return 0, {'error': str(e)}


def final_score(text1, text2, fuzzy_th):
    """Compute the S-score between two raw markdown documents.

    Extracts each document's ToC with `toc_extract`, then delegates to `proc`
    (using its default `difs`/`sim` settings).

    Parameters
    ----------
    text1, text2 : str
        Raw markdown source of the two documents.
    fuzzy_th : float in [0, 100]
        Threshold for fuzzy heading matching; see `proc`.

    Returns
    -------
    (s_score, debug_info)
        Same pair returned by `proc`.
    """
    toc1, toc_dict1 = toc_extract(text1)
    toc2, toc_dict2 = toc_extract(text2)
    s_score, debug_info = proc(toc1, toc2, toc_dict1, toc_dict2, fuzzy_th)
    return s_score, debug_info

# AWS Textract Extractor

Amazon's cloud-based document analysis service for extracting text, tables, and forms from documents.

## Features

- High-accuracy OCR
- Table extraction
- Form data extraction (key-value pairs)
- Layout analysis
- Handwriting recognition
- Configurable markdown output

## Installation

```bash
uv sync --group textract
```

## Getting Your Credentials

AWS Textract requires an AWS account, an S3 bucket, and AWS credentials:

1. **Create an AWS account** (if you don't have one): go to [aws.amazon.com](https://aws.amazon.com/) and click "Create an AWS Account". A free tier is available but Textract itself is a paid service.

2. **Create an S3 bucket** for Textract's temporary storage:
   - Go to the [S3 Console](https://s3.console.aws.amazon.com/s3/buckets)
   - Click "Create bucket", pick a name and region
   - Note the bucket name — you'll use it as `s3://your-bucket-name/textract-workspace/`

3. **Get your AWS credentials** (one of these methods):
   - **AWS CLI** (recommended): [Install the AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html), then run `aws configure` to set up your credentials
   - **Access keys**: Go to [IAM Console](https://console.aws.amazon.com/iam/) → Users → your user → Security Credentials → Create Access Key
   - **IAM Identity Center (SSO)**: If your organization uses SSO, follow your admin's instructions

4. **Set the IAM permissions** listed in the [IAM Permissions](#iam-permissions) section below.

## Environment Variables

### Required

- **`TEXTRACT_S3_WORKSPACE`** (required)
  - Full S3 URI for Textract workspace
  - Format: `s3://bucket-name/textract-workspace/`
  - Textract needs S3 for temporary file storage during processing
  - Make sure your AWS credentials have read/write access to this bucket

- **AWS Credentials** (required, via standard AWS SDK methods):
  - Option 1: AWS CLI profile
    - `AWS_PROFILE=your-profile-name`
  - Option 2: Direct credentials
    - `AWS_ACCESS_KEY_ID=your-access-key`
    - `AWS_SECRET_ACCESS_KEY=your-secret-key`
  - Option 3: AWS credentials file
    - `~/.aws/credentials`

### Example Setup

```bash
# Using AWS Profile
export TEXTRACT_S3_WORKSPACE="s3://my-bucket/textract-workspace/"
export AWS_PROFILE="default"

# Or using direct credentials
export TEXTRACT_S3_WORKSPACE="s3://my-bucket/textract-workspace/"
export AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
export AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
export AWS_DEFAULT_REGION="us-east-1"
```

## Configuration Options

### Basic Options

- **Features**: Enable Textract analysis features
  - `LAYOUT`: Document layout analysis
  - `TABLES`: Table extraction
  - `FORMS`: Form field extraction
  - `QUERIES`: Natural language queries
  - `SIGNATURES`: Signature detection

- **Hide Header/Footer**: Remove headers and footers from output

### Advanced Options

- **Hide Elements**: Control visibility of figures, tables, key-value pairs, page numbers
- **Table Options**: Column headers, captions, footers
- **Text Formatting**: Max consecutive newlines, title/section prefixes

## Usage

### Programmatic

```python
from benchmarkdown.extractors.textract import Extractor, Config

# Create configuration
config = Config(
    s3_upload_path="s3://my-bucket/textract-workspace/",
    features=["LAYOUT", "TABLES"],
    hide_header_layout=True,
    hide_footer_layout=True
)

# Create extractor
extractor = Extractor(config=config)

# Extract markdown
markdown = await extractor.extract_markdown("document.pdf")
```

### Via UI

1. Set environment variables (see above)
2. Launch the app: `uv run python app.py`
3. Select "AWS Textract" from the engine dropdown
4. Configure options (or load a saved profile)
5. Add to extraction queue
6. Upload documents and run extraction

## IAM Permissions

Your AWS credentials need the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "textract:AnalyzeDocument",
        "textract:StartDocumentAnalysis",
        "textract:GetDocumentAnalysis"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::your-bucket/textract-workspace/*"
    }
  ]
}
```

## Pricing

AWS Textract is a paid cloud service. Pricing depends on:
- Number of pages processed
- Features enabled (LAYOUT, TABLES, FORMS, etc.)
- Request volume

Check current pricing: https://aws.amazon.com/textract/pricing/

## Resources

- [Official Documentation](https://aws.amazon.com/textract/)
- [Textractor Library](https://github.com/aws-samples/amazon-textract-textractor)
- [AWS Console](https://console.aws.amazon.com/textract/)

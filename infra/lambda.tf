# --- SHAP explainability Lambda (container image; shap/sklearn are too big for a zip layer) ---

resource "aws_ecr_repository" "shap_lambda" {
  name = "${var.project_name}-shap-lambda"
  tags = var.tags
}

resource "aws_iam_role" "lambda_exec" {
  name = "${var.project_name}-shap-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "shap_explainer" {
  function_name = "${var.project_name}-shap-explainer"
  role          = aws_iam_role.lambda_exec.arn
  package_type  = "Image"
  # Build & push this image first: see infra/README.md
  image_uri = "${aws_ecr_repository.shap_lambda.repository_url}:latest"
  timeout   = 60
  memory_size = 2048
  tags      = var.tags

  lifecycle {
    ignore_changes = [image_uri] # image pushed out-of-band by CI/deploy script
  }
}

resource "aws_cloudwatch_log_group" "shap_lambda" {
  name              = "/aws/lambda/${aws_lambda_function.shap_explainer.function_name}"
  retention_in_days = 30
  tags              = var.tags
}

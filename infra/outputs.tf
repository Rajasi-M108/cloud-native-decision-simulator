output "frontend_url" {
  value = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}

output "api_load_balancer_dns" {
  value = aws_lb.api.dns_name
}

output "ecr_api_repository_url" {
  value = aws_ecr_repository.api.repository_url
}

output "ecr_shap_lambda_repository_url" {
  value = aws_ecr_repository.shap_lambda.repository_url
}

output "cognito_user_pool_id" {
  value = aws_cognito_user_pool.main.id
}

output "cognito_app_client_id" {
  value = aws_cognito_user_pool_client.main.id
}

output "rds_endpoint" {
  value     = aws_db_instance.main.address
  sensitive = true
}

output "raw_data_bucket" {
  value = aws_s3_bucket.raw_data.bucket
}

output "processed_data_bucket" {
  value = aws_s3_bucket.processed_data.bucket
}

output "frontend_bucket" {
  value = aws_s3_bucket.frontend.bucket
}

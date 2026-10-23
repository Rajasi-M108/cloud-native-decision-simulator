# Cost-trimmed: single-AZ, no read replica. Multi-AZ and a replica each add a
# full second paid instance (not covered by free tier) — fine to add back
# later (set multi_az = true, uncomment the replica) once this isn't a
# budget-constrained student deployment.

resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-db-subnets"
  subnet_ids = aws_subnet.private[*].id
  tags       = var.tags
}

resource "aws_db_instance" "main" {
  identifier              = "${var.project_name}-db-${var.environment}"
  engine                  = "postgres"
  engine_version          = "15"
  instance_class          = var.db_instance_class # db.t3.micro: free-tier eligible, 750 hrs/month for 12 months
  allocated_storage       = 20                     # free tier covers up to 20GB gp2/gp3
  storage_type            = "gp3"
  storage_encrypted       = true
  db_name                 = "bpi"
  username                = var.db_username
  password                = var.db_password
  db_subnet_group_name    = aws_db_subnet_group.main.name
  vpc_security_group_ids  = [aws_security_group.rds.id]
  multi_az                = false # keep single instance to stay within free tier
  publicly_accessible     = false
  backup_retention_period = 1
  skip_final_snapshot     = true # set false for a real production cutover
  deletion_protection     = false
  tags                    = var.tags
}

# --- Read replica (disabled by default — costs a second full instance) ---
# Uncomment once you're past free-tier constraints and dashboard query load
# actually warrants offloading reads from the primary.
#
# resource "aws_db_instance" "read_replica" {
#   identifier             = "${var.project_name}-db-replica-${var.environment}"
#   replicate_source_db    = aws_db_instance.main.identifier
#   instance_class         = var.db_instance_class
#   publicly_accessible    = false
#   vpc_security_group_ids = [aws_security_group.rds.id]
#   tags                   = var.tags
# }

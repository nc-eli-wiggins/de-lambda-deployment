resource "aws_instance" "jenkins" {
    ami             = "ami-07c1b39b7b3d2525d"
    instance_type   = "t2.micro"
    key_name        = "<name of your key_pair here>"
    
    vpc_security_group_ids = [ aws_security_group.jenkins_traffic.id ]

    iam_instance_profile = aws_iam_instance_profile.ec2_instance_profile.name

    user_data = <<-EOF
              #!/bin/bash
              sudo apt update
              sudo apt install openjdk-8-jdk -y
              
              EOF

}

resource "aws_security_group" "jenkins_traffic" {
  name        = "jenkins_master_group"
  description = "Allow SSH, HTTP, and HTTPS traffic"

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

output "instance_public_ip" {
  description = "IP of instance for ssh connection"
  value       = aws_instance.jenkins.public_ip
}
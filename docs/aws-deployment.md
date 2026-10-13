**AWS Account Preparation**

Completed

~~Created an IAM user named iamadmin with administrative permissions for infrastructure setup.~~

~~Enabled MFA for iamadmin.~~

~~Created an AWS monthly cost budget with spending alerts.~~

Configure the AWS CLI authentication method.

Provision the project infrastructure using Terraform.

**Security Notes**

* Do not commit AWS access keys, secret keys, passwords, or other credentials.

* The application's AWS permissions will use dedicated IAM roles with least-privilege access.

* Cost budget notifications are alerts, not hard spending limits.

* Deployment Region

* Planned region: US East (N. Virginia), us-east-1.
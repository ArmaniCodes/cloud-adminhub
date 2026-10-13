**AWS Account Preparation**

Completed

~~Installed Terraform in the Ubuntu/WSL environment.~~

~~Configured AWS CLI browser-based authentication using aws login.~~

~~Verified the AWS identity using aws sts get-caller-identity.~~

~~Configured the cloudadminhub AWS CLI profile.~~

~~Created a terraform-cloudadminhub profile that obtains credentials through the AWS CLI credential_process mechanism.~~

~~Configured the Terraform profile to use us-east-1 (US East, N. Virginia).~~

**Authentication**

Terraform uses the terraform-cloudadminhub profile, which obtains temporary credentials through the cloudadminhub AWS CLI profile.

Verify the authenticated identity:

```aws sts get-caller-identity --profile terraform-cloudadminhub```

The AWS CLI authentication session may expire and need to be renewed.

**Security Notes**

* Never commit AWS credentials, session tokens, access keys, or secret keys.

* Local AWS CLI profile configuration stays outside the project repository.

* Do not embed credentials in Terraform files or infrastructure resources.

* Review terraform plan before applying infrastructure changes.

**Next Milestone**

Create the initial Terraform configuration and define the VPC networking architecture.
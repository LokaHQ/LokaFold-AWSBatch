import os
from aws_cdk import core as cdk
from aws_cdk.core import (
    Construct
)
import aws_cdk.aws_iam as iam
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_kms as kms

class VpcStack(cdk.Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # KMS
        self.key = kms.Key(self, "EncryptionKey", enable_key_rotation=True)
        self.key.add_to_resource_policy(
            iam.PolicyStatement(
                actions=[
                    "kms:Create*",
                    "kms:Describe*",
                    "kms:Enable*",
                    "kms:List*",
                    "kms:Put*",
                    "kms:Update*",
                    "kms:Revoke*",
                    "kms:Disable*",
                    "kms:Get*",
                    "kms:Delete*",
                    "kms:TagResource",
                    "kms:UntagResource",
                    "kms:ScheduleKeyDeletion",
                    "kms:CancelKeyDeletion",
                ],
                resources=["*"],
                principals=[iam.AnyPrincipal()],
            ),
        )
        self.key.add_to_resource_policy(
            iam.PolicyStatement(
                actions=[
                    "kms:Encrypt",
                    "kms:Decrypt",
                    "kms:ReEncrypt*",
                    "kms:GenerateDataKey*",
                    "kms:DescribeKey",
                ],
                resources=["*"],
                principals=[iam.AnyPrincipal()],
            ),
        )
        self.key.add_to_resource_policy(
            iam.PolicyStatement(
                actions=[
                    "kms:Encrypt",
                    "kms:Decrypt",
                    "kms:ReEncrypt*",
                    "kms:GenerateDataKey*",
                    "kms:DescribeKey",
                ],
                resources=["*"],
                principals=[iam.AnyPrincipal()],
            ),
        )

        # Network Configuration
        vpc_id = os.environ.get("vpc_id", None)
        use_default_vpc = bool(int(os.environ.get("use_default_vpc", None)))
        
        if use_default_vpc: 
            self.vpc = ec2.Vpc.from_lookup(self, 'LokaFoldVPC', is_default=True)
            self.sg = os.environ.get("default_vpc_sg", None)
        elif vpc_id is None or vpc_id == '':

            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="PublicSubnet0",
                    subnet_type = ec2.SubnetType.PUBLIC,
                    cidr_mask = 26
                ),
                ec2.SubnetConfiguration(
                    name = "PrivateSubnet0",
                    subnet_type = ec2.SubnetType.PRIVATE,
                    cidr_mask = 26
                )
            ]

            self.vpc = ec2.Vpc(
                self,
                "LokaFoldVPC",
                cidr="10.0.0.0/16",
                max_azs=1,
                subnet_configuration=subnet_configuration,
            )

            self.public_route_table = ec2.CfnRouteTable(
                self, 
                "PublicRouteTable", 
                vpc_id=self.vpc.vpc_id,
            )

            self.private_route_table = ec2.CfnRouteTable(
                self,
                "PrivateRouteTable0",
                vpc_id=self.vpc.vpc_id,
            )

            self.public_route = ec2.CfnRoute(
                self,
                "PublicRoute",
                route_table_id=self.public_route_table.attr_route_table_id,
                destination_cidr_block="0.0.0.0/0",
                gateway_id=self.vpc.internet_gateway_id,
            )

            public_subnet_route_association = ec2.CfnSubnetRouteTableAssociation(
                self,
                "PublicSubnetRouteTableAssociation0",
                subnet_id=self.vpc.public_subnets[0].subnet_id,
                route_table_id=self.public_route_table.attr_route_table_id,
            )

            self.elastic_ip = ec2.CfnEIP(
                self,
                "ElasticIP0",
                domain="vpc",
            )

            self.nat_gateway = ec2.CfnNatGateway(
                self,
                "NATGateway0",
                subnet_id=self.vpc.public_subnets[0].subnet_id,
                allocation_id=self.elastic_ip.attr_allocation_id,
            )
            
            private_route_to_internet = ec2.CfnRoute(
                self,
                "PrivateRouteToInternet0",
                route_table_id=self.private_route_table.attr_route_table_id,
                destination_cidr_block="0.0.0.0/0",
                nat_gateway_id=self.nat_gateway.ref, # nategateway_id
            )

            private_subnet_route_association = ec2.CfnSubnetRouteTableAssociation(
                self,
                "PrivateSubnetRouteTableAssociation0",
                subnet_id=self.vpc.private_subnets[0].subnet_id,
                route_table_id=self.private_route_table.attr_route_table_id,
            )
            private_subnet_route_association.add_depends_on(public_subnet_route_association)

            endpoint = self.vpc.add_gateway_endpoint(
                "S3Endpoint", service=ec2.GatewayVpcEndpointAwsService.S3
            )
            self.sg = self.vpc.vpc_default_security_group
        else:
            self.vpc = ec2.Vpc.from_vpc_attributes(
                self,
                "LokaFoldVPC",
                vpc_id=vpc_id,
                availability_zones=[os.environ.get("az", None)],
                public_subnet_ids=[os.environ.get("public_subnet_0", None)],
                private_subnet_ids=[os.environ.get("private_subnet_0", None)],
                public_subnet_route_table_ids=[os.environ.get("public_route_table", None)],
                private_subnet_route_table_ids=[os.environ.get("private_route_table", None)]
            )

            self.private_subnet = self.vpc.public_subnets[0]
            self.public_subnet = self.vpc.private_subnets[0]
            self.sg = os.environ.get("default_vpc_sg", None)

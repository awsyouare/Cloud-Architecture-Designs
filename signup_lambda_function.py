import json
import logging
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('customer_details')
table1 = dynamodb.Table('waiting_list')

##email notification
SENDER = 'joedomain@live.com'
AWS_REGION = "us-east-1"

##Create a new SES resource and specify a region.
client = boto3.client('ses',region_name=AWS_REGION ) 


##defining the lambda function
def lambda_handler(event, context):
    logger.info('Received message: %s', event)
    http_method = event.get('httpMethod')
   
    ##defining the function condition
    path = (event.get('path').split("/")[1]) 
    
    ##function condition_1
    if http_method == 'OPTIONS':
        response = {
            'statusCode': 200,
            'headers': {
                    'Content-Type' : 'application/json',
                    'Access-Control-Allow-Origin' : '*',
                    'Allow' : 'OPTIONS, POST,GET',
                    'Access-Control-Allow-Methods' : 'OPTIONS, POST,GET',
                    'Access-Control-Allow-Headers' : '*'}
            } 
    ##function condition_2
    elif path == "update-status":
        data = table1.get_item(Key={'id': '1'})
        if 'Item' in data :
            data = data['Item']
            current_number = data['current_number']
            try:
                update_item = table1.update_item(
                                        Key={'id': '1'},
                                        UpdateExpression="set current_number=:cn",
                                        ExpressionAttributeValues={':cn': (current_number+1)},
                                        ReturnValues="UPDATED_NEW"
                            )
                res_item='Updated status : '+str(current_number+1)
            ##error handling     
            except:
                res_item='Error whle saving data'
        response = {
                'statusCode': 200,
                'headers': {
                    'Content-Type' : 'application/json',
                    'Access-Control-Allow-Origin' : '*',
                    'Allow' : 'POST',
                    'Access-Control-Allow-Methods' : 'OPTIONS, POST',
                    'Access-Control-Allow-Headers' : '*'},
                'body': json.dumps(res_item)}
                
    else:
        body = event.get('body')
        email = ''
        lastname = ''
        if body is not None:
            email = json.loads(body).get('email', email)
            lastname = json.loads(body).get('lastname', lastname)
            
            
            data = table.get_item(Key={'email': email})
            if 'Item' in data :
                data = data['Item']
                waiting_list = str(data['prov_number'])
                data = table1.get_item(Key={'id': '1'})
                if 'Item' in data :
                    data = data['Item']
                    current_number = str(data['current_number'])
                res_item={"status":"ok","message":"Signed-Up","current_number":current_number,"waiting_list":waiting_list}
                
            else:
                data = table1.get_item(Key={'id': '1'})
                if 'Item' in data :
                    data = data['Item']
                    current_number = str(data['current_number'])
                    prov_number = data['prov_number']
                    try:
                        table.put_item(Item={'email' : email,'lastname': lastname,'prov_number':(prov_number+1)})
                        update_item = table1.update_item(
                                        Key={'id': '1'},
                                        UpdateExpression="set prov_number=:pn",
                                        ExpressionAttributeValues={':pn': (prov_number+1)},
                                        ReturnValues="UPDATED_NEW"
                            )
                        
                        ##email notification
                        SUBJECT = "Email List Successfull SignUp"
                        RECIPIENT = email
                        ##The email body for recipients with non-HTML email clients.
                        BODY_TEXT = "Hello,\r\nSignup done for email :"+email
        
                        ##The HTML body of the email.
                        BODY_HTML = """\
                                    <html>
                                    <head></head>
                                    <p dir="ltr" style="line-height:1.2;margin-top:0pt;margin-bottom:0pt;"><span style="font-size:12pt;font-family:Calibri,sans-serif;color:#000000;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;">Thank-you for Signing-Up to our email list, your email is now registered.</span></p>
                                    <p dir="ltr" style="line-height:1.2;margin-top:0pt;margin-bottom:0pt;"><br></p>
                                    </html>
                                    """ 
                        ##The character encoding for the email.
                        CHARSET = "utf-8"
                        try:
                            response=client.send_email(
                            Destination={'ToAddresses': [RECIPIENT,],},
                            Message={
                                'Body': {
                                    'Html': {
                                        'Charset': CHARSET,
                                        'Data': BODY_HTML,
                                        },
                                    'Text': {
                                        'Charset': CHARSET,
                                        'Data': BODY_TEXT,
                                    },
                                },
                                'Subject': {
                                    'Charset': CHARSET,
                                    'Data': SUBJECT,
                                },
                            },
                            Source=SENDER,
                            )
                            print("Email sent! Message ID:",response['MessageId'])
                        ##Display an error if something goes wrong. 
                        except ClientError as e:
                            print(e.response['Error']['Message'])
                        ##    
                        res_item={"status":"ok","message":"Signed-Up","current_number":current_number,"waiting_list":str(prov_number+1)}
                    except:
                        res_item='Error while saving data'+str(prov_number)
        
        response = {
            'statusCode': 200,
            'headers': {
                    'Content-Type' : 'application/json',
                    'Access-Control-Allow-Origin' : '*',
                    'Allow' : 'POST',
                    'Access-Control-Allow-Methods' : 'OPTIONS, POST',
                    'Access-Control-Allow-Headers' : '*'},
            'body': json.dumps(res_item)
            } 
       
    logger.info("Response: %s", response)
    return response
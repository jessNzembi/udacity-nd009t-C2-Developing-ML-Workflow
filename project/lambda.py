####################################
####### serialize Image Data #######


import json
import boto3
import base64


s3 = boto3.client('s3')

def lambda_handler(event, context):
    """A function to serialize target data from S3"""

    # Get the s3 address from the Step Function event input
    key = event['s3_key']
    bucket = event['s3_bucket']

    # Download the data from s3 to /tmp/image.png
    s3.download_file(bucket, key, "/tmp/image.png")

    # We read the data from a file
    with open("/tmp/image.png", "rb") as f:
        image_data = base64.b64encode(f.read())

    # Pass the data back to the Step Function
    print("Event:", event.keys())
    return {
        'statusCode': 200,
        'body': {
            "image_data": image_data,
            "s3_bucket": bucket,
            "s3_key": key,
            "inferences": []
        }
    }


##########################
####### Classifier #######


import json
# import sagemaker
import base64
import boto3

# Fill this in with the name of your deployed model
ENDPOINT = "image-classification-2024-09-26-14-33-40-302"

def lambda_handler(event, context):

    params    = event['body']
    image     = params['image_data']
    s3_bucket = params['s3_bucket']
    s3_key    = params['s3_key']


    # Decode the image data
    image = base64.b64decode(image) 
    
    runtime = boto3.client("runtime.sagemaker")

    response = runtime.invoke_endpoint(
                                    EndpointName = ENDPOINT,
                                    ContentType  = "image/png",
                                    Body= image
                                    )
    
    # return the data back to the Step Function
    inferences = json.loads(response['Body'].read().decode())
    event['inferences'] = inferences
    
    return {
        'statusCode': 200,
        'body': {
            "image_data": params['image_data'],
            "s3_bucket": s3_bucket,
            "s3_key": s3_key,
            "inferences": inferences
        }
    }



##############################
####### Filter Results #######


import json

THRESHOLD = .93

def lambda_handler(event, context):

    # Grab the inferences from the event
    inferences = event["body"]["inferences"]

    # Check if any values in our inferences are above THRESHOLD
    meets_threshold = False
    for inference in inferences:
        if inference > THRESHOLD:
            meets_threshold = True

    # If our threshold is met, pass our data back out of the
    # Step Function, else, end the Step Function with an error
    if meets_threshold:
        pass
    else:
        raise("THRESHOLD_CONFIDENCE_NOT_MET")

    return {
        'statusCode': 200,
        'body': json.dumps(event)
    }
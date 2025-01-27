

# Deploy the model to SageMaker Inference
"""

import logging
import boto3
from botocore.exceptions import ClientError
import os
from sagemaker import image_uris
from sagemaker.model import Model
from datetime import datetime
import os
import numpy as np
import pandas as pd
import json

np.random.seed(2)

from PIL import Image
from pylab import *
from PIL import Image, ImageChops, ImageEnhance

"""### Initialize variables"""

aws_region='ca-central-1'
s3_bucket = 'tamperingdetection' + datetime.datetime.utcnow().strftime("%d-%m-%Y-%H%M%S")
model_s3_key = 'model.tar.gz'
framework='tensorflow'
version = '2.6'
initial_instance_count=1
instance_type='ml.m5.xlarge'
py_version='py38'
image_scope='inference'
models_dir = 'model'
models_artifact = '1'
path_to_archive_content = os.path.join(models_dir, models_artifact)
s3_client = boto3.client('s3')

"""### Create S3 bucket"""

s3_client.create_bucket(
    Bucket=s3_bucket,
    CreateBucketConfiguration={
        'LocationConstraint': aws_region
    }
)

"""### Create model artifact archive"""

!tar -czvf model.tar.gz model/1

"""Create a tar.gz file from the model artifacts. We have saved the model artifacts as a directory named “1” containing serialized signatures and the state needed to run them, including variable values and vocabularies to deploy to Amazon SageMaker runtime. You can also include a custom inference file inference.py within the 'code' folder in the model artifact. The custom inference can be used for pre / post processing of the input image

### Upload the model artifact to S3
"""

def upload_file(file_name, bucket, object_name=None):

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

is_uploaded = upload_file(model_s3_key, s3_bucket, None)

"""### Create the SageMaker Inference Endpoint"""

container = image_uris.retrieve(region=aws_region,
                                framework=framework,
                                version=version,
                                image_scope=image_scope,
                                py_version=py_version,
                                instance_type =instance_type)

model_url = f's3://{s3_bucket}/{model_s3_key}'

model = Model(image_uri=container,
              model_data=model_url,
              role=sagemaker_role)

endpoint_name = f"tamperingdetection-{datetime.datetime.utcnow():%Y-%m-%d-%H%M}"
print("EndpointName =", endpoint_name)

model.deploy(
    initial_instance_count=initial_instance_count,
    instance_type=instance_type,
    endpoint_name=endpoint_name
)

"""### Test the Inference endpoint"""

def convert_to_ela_image(path, quality):
    filename = path
    resaved_filename = 'tempresaved.jpg'
    im = Image.open(filename)
    bm = im.convert('RGB')
    im.close()
    im=bm
    im.save(resaved_filename, 'JPEG', quality = quality)
    resaved_im = Image.open(resaved_filename)
    ela_im = ImageChops.difference(im, resaved_im)
    extrema = ela_im.getextrema()
    max_diff = max([ex[1] for ex in extrema])
    if max_diff == 0:
        max_diff = 1
    scale = 255.0 / max_diff
    ela_im = ImageEnhance.Brightness(ela_im).enhance(scale)
    im.close()
    bm.close()
    resaved_im.close()
    del filename
    del resaved_filename
    del im
    del bm
    del resaved_im
    del extrema
    del max_diff
    del scale
    return ela_im

sagemaker_runtime = boto3.client(
    "sagemaker-runtime", region_name=aws_region)

endpoint_name=endpoint_name

def check_image(image):

    X = []
    X.append(array(convert_to_ela_image(image, 90).resize((128, 128))).flatten() / 255.0)
    X = np.array(X)

    X = X.reshape(-1, 128, 128, 3)

    data = {'instances': X.tolist()}

    # Gets inference from the model hosted at the specified endpoint:
    response = sagemaker_runtime.invoke_endpoint(
        EndpointName=endpoint_name,
        Body=json.dumps(data),
        ContentType="application/json"
        )

    # Decodes and prints the response body:
    #print(response['Body'].read().decode('utf-8'))
    predictions_res = json.loads(response['Body'].read().decode('utf-8'))
    predictions = predictions_res['predictions']

    print(predictions)

    pred_classes = np.argmax(predictions,axis = 1)
    print(pred_classes)

check_image('images/predict/Paystub.jpg')

check_image('images/predict/TamperedPaystub.jpg')

"""### Cleanup"""

# delete sagemaker inference endpoint
client = boto3.client('sagemaker')
client.delete_endpoint(
    EndpointName=endpoint_name
)

# empty s3 bucket and delete the bucket
s3_resource = boto3.resource('s3')
bucket = s3_resource.Bucket(s3_bucket)
bucket.objects.all().delete()
bucket.delete()
print("S3 bucket and contents deleted")


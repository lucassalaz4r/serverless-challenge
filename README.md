# serverless-challenge

This image analyzer serverless application implements the architecture in the image below using [Python](https://www.python.org/) and [Serverless Framework](https://www.serverless.com/framework/docs/).

![Architecture](Architecture.png)

When an image is uploaded to the **S3** bucket inside the ```uploads/``` folder, the ```extractMetadata``` handler is triggered, extracting the image metadata and storing it in a **DynamoDB** table. The image metadata can be accessed via an **API Gateway** endpoint, triggering the ```getMetadata``` handler, which returns the metadata of the requested image.

Two more **API Gateway** handlers were implemented, ```getImage``` and ```infoImages```. You can check the handler functions in detail in the **Handlers** topic right below.

Check the **API Endpoints** topic for more detail about the application API.

Infrastructure changes in ```serverless.yml``` so the app could run correctly, are detailed in the **Infrastructure Changes** topic.

## Setup
Make sure you have [Serverless Framework](https://www.serverless.com/framework/docs/getting-started) installed on your machine, then clone this repository and go into its directory.
```
git clone https://github.com/lucassalaz4r/serverless-challenge.git
cd serverless-challenge
```

Create your AWS credentials following [this tutorial](https://www.youtube.com/watch?v=KngM5bfpttA), save the **access key** and the **secret key** in a file, then configure the profile **hackathon** with the command below replacing "Your access key" and "Your secret key" with the corresponding keys:
```
serverless config credentials \
  --provider aws \
  --key "Your access key" \
  --secret "Your secret key" \
  --profile hackathon
```

Now you're able to deploy the application to a development stage with,
```
serverless deploy --stage dev
```
or to a production stage with:
```
serverless deploy --stage production
```

## API Endpoints

---

### ```GET images/file/{s3objectkey}```
#### **Request**
Key | Required | Value | Description
---|---|---|---
s3objectkey | required | cat.jpg | Image file name

#### **Response**
The requested image file.

#### **Example Response**
![Cat](cat.jpg)

---

### ```GET images/info```
#### **Response**
Key | Description
---|---
highestSizeImage | Path/key of the image with the highest size
lowestSizeImage | Path/key of the image with the lowest size
contentTypes | MIME media type count

#### **Example Response**
```
{
  "highestSizeImage": "uploads/duck.gif",
  "lowestSizeImage": "uploads/spider.jpg",
  "contentTypes": {
    "image/png": 1,
    "image/jpeg": 4,
    "image/gif": 1
  }
}
```

---

### ```GET images/metadata/{s3objectkey}```
#### **Request**
Key | Required | Value | Description
---|---|---|---
s3objectkey | required | cat.jpg | Image file name

#### **Response**
Key | Description
---|---
s3objectkey | S3 image object key
size | Image size in bytes
contentType | MIME media type
width | Width in pixels
height | Height in pixels

#### **Example Response**
```
{
  "s3objectkey": "uploads/cat.jpg",
  "size": "828201",
  "contentType": "image/jpeg",
  "width": "1680",
  "height": "1050"
}
```

## Handlers

---

### ```extractMetadata(event, context)```
Triggered when a **jpg**, **png**, or **gif** image is uploaded to the folder ```/uploads``` inside the S3 bucket. It extracts the **s3objectkey**, **size**, **contentType**, **width**, and **height** of the created image and stores this metadata in a DynamoDB table.
#### **Parameters**
 - **event** - S3 create object event.
 - **context** - AWS context object.
#### **Return type**
 - dict
#### **Returns**
```
{
  "s3objectkey": "string",
  "size": "string",
  "contentType": "string",
  "width": "string",
  "height": "string"
}
```

---

### ```getMetadata(event, context)```
Triggered when a ```GET``` request hits the endpoint ```images/metadata/{s3objectkey}```. Retrieves the requested image metadata from the DynamoDB table and returns it as a response.
#### **Parameters**
 - **event** - API Gateway event object.
 - **context** - AWS context object.
#### **Return type**
 - dict
#### **Returns**
```
{
  "statusCode": 200,
  "body": {
    "s3objectkey": "string",
    "size": "string",
    "contentType": "string",
    "width": "string",
    "height": "string"
  }
}
```

---

### ```getImage(event, context)```
Triggered when a ```GET``` request hits the endpoint ```images/file/{s3objectkey}```. It downloads the requested image to the ```/tmp``` folder if it isn't already there and returns the image as a response.
#### **Parameters**
 - **event** - API Gateway event object.
 - **context** - AWS context object.
#### **Return type**
 - dict
#### **Returns**
```
{
  "statusCode": 200,
  "body": image binary data,
  "headers": {
    "Content-Type": "string",
  },
  "isBase64Encoded": True,
}
```

---

### ```infoImages(event, context)```
Triggered when a ```GET``` request hits the ```images/info``` endpoint. Retrieves the names of the images with the highest and lowest size in bytes, and the count of the different image types, and returns this data as a response.
#### **Parameters**
 - **event** - API Gateway event object.
 - **context** - AWS context object.
#### **Return type**
 - dict
#### **Returns**
```
{
  "statusCode": 200,
  "body": {
    "highestSizeImage": "string",
    "lowestSizeImage": "string",
    "contentTypes": {
      <MIME media type 1>: 123,
      <MIME media type 2>: 123
      ...
    }
  }
}
```

## Infrastructure Changes
This topic covers changes made in the ```serverless.yml``` file when compared with the original file from before I started the challenge. Almost all of the changes were needed so the application could run correctly.

---

### **Runtime**
Python3.6 is deprecated in AWS, so I changed the runtime to Python3.9.
```
runtime: python3.9
```

---

### **Binary media types**
I added to API Gateway support for all binary media types, in order to be able to return images via API.
```
apiGateway:
  binaryMediaTypes:
    - '*/*'
```

---

### **Layers**
The application uses the lib [Pillow](https://python-pillow.org/) to extract the height and width from the images, so I configured a layer for Pillow, so the application is able to use the library.
```
layers:
  - arn:aws:lambda:us-east-1:770693421928:layer:Klayers-p39-pillow:1
```

---

### **Environment variables**
I added two more environment variables ```BUCKET_NAME``` and ```S3_RULE_PREFIX```.
```
environment:
  BUCKET_NAME: ${self:service}-${opt:stage, self:provider.stage}-instagrao
  DYNAMODB_TABLE: ${self:service}-${opt:stage, self:provider.stage}
  S3_RULE_PREFIX: uploads/
```

---

### **IAM Role Statements**
I added an effect to allow handlers to access S3 objects.
```
- Effect: Allow
  Action:
    - 's3:GetObject'
  Resource:
    - 'arn:aws:s3:::${self:provider.environment.BUCKET_NAME}/*'
```

---

### **Functions**
---
#### ```extractMetadata```
I changed the bucket and the rule prefix of the S3 events to their respective environment variables. Added 3 more S3 events for images with the suffixes .jpeg, .png, and .gif.

```
events:
  - s3:
      bucket: ${self:provider.environment.BUCKET_NAME}
      event: s3:ObjectCreated:*
      rules:
        - prefix: ${self:provider.environment.S3_RULE_PREFIX}
        - suffix: .jpg
  - s3:
      bucket: ${self:provider.environment.BUCKET_NAME}
      event: s3:ObjectCreated:*
      rules:
        - prefix: ${self:provider.environment.S3_RULE_PREFIX}
        - suffix: .jpeg
  - s3:
      bucket: ${self:provider.environment.BUCKET_NAME}
      event: s3:ObjectCreated:*
      rules:
        - prefix: ${self:provider.environment.S3_RULE_PREFIX}
        - suffix: .png
  - s3:
      bucket: ${self:provider.environment.BUCKET_NAME}
      event: s3:ObjectCreated:*
      rules:
        - prefix: ${self:provider.environment.S3_RULE_PREFIX}
        - suffix: .gif
```

---
#### ```getMetadata```
Changed the previous API endpoint to ```images/metadata/{s3objectkey}```.
```
getMetadata:
    handler: handler.getMetadata
    description:
    memorySize: 128
    timeout: 30
    events:
      - http:
          path: images/metadata/{s3objectkey}
          method: get
          cors: true
```

---
#### ```getImage```
This is a new lambda added, which the handler is ```handler.getImage```.
```
getImage:
  handler: handler.getImage
  description:
  memorySize: 128
  timeout: 30
  events:
    - http:
        path: images/file/{s3objectkey}
        method: get
        cors: true
```

---
#### ```infoImages```
This is a new lambda added, which the handler is ```handler.infoImages```.
```
infoImages:
  handler: handler.infoImages
  description:
  memorySize: 128
  timeout: 30
  events:
    - http:
        path: images/info
        method: get
        cors: true
```
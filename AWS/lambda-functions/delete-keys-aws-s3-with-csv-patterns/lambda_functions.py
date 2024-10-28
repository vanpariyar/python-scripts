import boto3
import csv
import os

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    # Define bucket name and path to local CSV file
    bucket_name = os.getenv('TARGET_BUCKET')  # Bucket where objects are to be deleted
    csv_file_path = 'patterns.csv'  # Local path within Lambda for the CSV file

    try:
        # Read the CSV file from the Lambda's local storage
        patterns = []
        with open(csv_file_path, mode='r') as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                patterns.append(row[0])  # Assuming each row has one pattern

        delete_responses = []

        for prefix in patterns:
            # List objects with the specific prefix in S3
            response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
            if 'Contents' not in response:
                print(f"No objects found with prefix '{prefix}' in bucket '{bucket_name}'.")
                continue

            # Extract keys of objects with the prefix
            keys_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]

            # Batch delete objects (max 1000 keys per batch)
            while keys_to_delete:
                batch = keys_to_delete[:1000]
                keys_to_delete = keys_to_delete[1000:]

                # Delete the batch of objects
                delete_response = s3_client.delete_objects(
                    Bucket=bucket_name,
                    Delete={'Objects': batch}
                )
                delete_responses.append(delete_response)

        return {"message": "Objects deleted successfully", "details": delete_responses}

    except Exception as e:
        return {"message": "Error deleting objects", "error": str(e)}

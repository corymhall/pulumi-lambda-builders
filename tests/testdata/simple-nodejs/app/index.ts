import { DynamoDBClient, DescribeTableCommand } from '@aws-sdk/client-dynamodb';

export async function handler() {
  const client = new DynamoDBClient();
  const input = {
    TableName: process.env.TABLE_NAME,
  };
  const command = new DescribeTableCommand(input);
  const response = await client.send(command);
  console.log(response);
}

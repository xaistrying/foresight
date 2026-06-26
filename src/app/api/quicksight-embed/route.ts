import { NextResponse } from "next/server";
import {
  QuickSightClient,
  GenerateEmbedUrlForAnonymousUserCommand,
} from "@aws-sdk/client-quicksight";

const client = new QuickSightClient({
  region: process.env.AWS_REGION ?? "ap-southeast-1",
  credentials: {
    accessKeyId:     process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
  },
});

export async function GET() {
  const accountId   = process.env.QUICKSIGHT_AWS_ACCOUNT_ID!;
  const dashboardId = process.env.QUICKSIGHT_DASHBOARD_ID!;
  const namespace   = process.env.QUICKSIGHT_NAMESPACE ?? "default";

  if (!accountId || !dashboardId) {
    return NextResponse.json(
      { error: "Missing QUICKSIGHT_AWS_ACCOUNT_ID or QUICKSIGHT_DASHBOARD_ID in env" },
      { status: 500 }
    );
  }

  try {
    const command = new GenerateEmbedUrlForAnonymousUserCommand({
      AwsAccountId: accountId,
      Namespace: namespace,
      SessionLifetimeInMinutes: 60,
      AuthorizedResourceArns: [
        `arn:aws:quicksight:${process.env.AWS_REGION ?? "ap-southeast-1"}:${accountId}:dashboard/${dashboardId}`,
      ],
      ExperienceConfiguration: {
        Dashboard: {
          InitialDashboardId: dashboardId,
        },
      },
    });

    const response = await client.send(command);

    return NextResponse.json({ embedUrl: response.EmbedUrl });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    console.error("[QuickSight embed]", message);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

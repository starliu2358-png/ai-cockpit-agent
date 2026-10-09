import type { Answer, FeedbackValue, VehicleOption } from "./types";

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = "服务暂时不可用，请稍后重试。";
    try {
      const payload = (await response.json()) as { detail?: string };
      message = payload.detail || message;
    } catch {
      // Keep the safe generic message for non-JSON failures.
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export async function fetchVehicles(): Promise<VehicleOption[]> {
  return parseResponse<VehicleOption[]>(await fetch("/api/v1/vehicles"));
}

export async function askQuestion(question: string, trimId: string): Promise<Answer> {
  return parseResponse<Answer>(
    await fetch("/api/v1/answers", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, trimId }),
    }),
  );
}

export async function sendFeedback(
  answerId: string,
  value: FeedbackValue,
): Promise<FeedbackValue> {
  const response = await parseResponse<{ value: FeedbackValue }>(
    await fetch(`/api/v1/answers/${answerId}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ value }),
    }),
  );
  return response.value;
}

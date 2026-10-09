export type VehicleOption = {
  trimId: string;
  displayName: string;
  model: string;
};

export type Citation = {
  id: string;
  title: string;
  section: string;
  url: string;
  retrievedAt: string;
};

export type Answer = {
  answerId: string;
  answer: string;
  boundaryResult: "supported" | "unsupported" | "unconfirmed" | null;
  citations: Citation[];
  speechText: string;
  fallbackReason: string | null;
};

export type FeedbackValue = "up" | "down";

// Allow @fal-ai/client without its own type declarations
declare module "@fal-ai/client" {
  export interface FalConfig {
    credentials?: string;
  }
  export interface QueueUpdate {
    status: string;
    logs?: Array<{ message: string }>;
  }
  export interface SubscribeOptions {
    input: Record<string, unknown>;
    logs?: boolean;
    onQueueUpdate?: (update: QueueUpdate) => void;
  }
  export interface FalResult {
    data: unknown;
    requestId: string;
  }
  export interface StorageClient {
    upload(file: File): Promise<string>;
  }
  export interface FalClient {
    config(options: FalConfig): void;
    subscribe(modelId: string, options: SubscribeOptions): Promise<FalResult>;
    storage: StorageClient;
  }
  export const fal: FalClient;
}

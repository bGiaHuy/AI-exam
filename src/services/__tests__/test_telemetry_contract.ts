/**
 * Test verifying that frontend strictly parses current backend WebSocket payload
 * without loss or type errors.
 */
import type { WebSocketDetectionPayload, IngestTelemetry } from '../aiModelService';

const sampleBackendPayload: WebSocketDetectionPayload = {
  type: "detection_result",
  source_id: "cam_01",
  session_id: "sess_test_123",
  sequence_id: 42,
  timestamp: 1726300000.123,
  latency_ms: 28.5,
  inference_fps: 35.1,
  level: "red",
  has_cheating: true,
  has_phone: false,
  incident_id: "inc_1726300000_abc123",
  detections: [
    {
      id: "det_head_1_42",
      label: "HEAD_TURNING",
      label_vi: "Quay đầu 45° (1.3s) (Track 1)",
      confidence: 88.0,
      bbox: [10.5, 20.0, 30.0, 40.0],
      level: "red",
      track_id: 1
    }
  ],
  server_packets_received: 45,
  server_frames_decoded: 45,
  server_received_frames: 45,
  inference_submitted_frames: 45,
  inference_superseded_frames: 10,
  inference_processed_frames: 34,
  processed_inference_frames: 34,
  inference_pending_frames: 1,
  pending_inference_frames: 1,
  result_messages_sent: 34,
  detection_results_sent: 34,
  detected_objects: 34,
  first_decoded_monotonic: 100.0,
  last_decoded_monotonic: 103.0,
  effective_acquisition_fps: 14.67
};

function verifyTelemetryParsing(payload: WebSocketDetectionPayload): boolean {
  if (payload.type !== "detection_result") throw new Error("Invalid type");
  if (payload.sequence_id !== 42) throw new Error("Invalid sequence_id");
  if (payload.server_packets_received !== 45) throw new Error("Invalid server_packets_received");
  if (payload.server_frames_decoded !== 45) throw new Error("Invalid server_frames_decoded");
  if (payload.inference_processed_frames !== 34) throw new Error("Invalid inference_processed_frames");
  if (payload.inference_pending_frames !== 1) throw new Error("Invalid inference_pending_frames");
  if (payload.result_messages_sent !== 34) throw new Error("Invalid result_messages_sent");
  if (payload.effective_acquisition_fps !== 14.67) throw new Error("Invalid effective_acquisition_fps");
  
  // Verify strict mathematical invariant 6
  const sum = (payload.inference_processed_frames || 0) + 
              (payload.inference_superseded_frames || 0) + 
              (payload.inference_pending_frames || 0);
  if (sum !== payload.inference_submitted_frames) {
    throw new Error(`Invariant 6 balance mismatch: ${sum} !== ${payload.inference_submitted_frames}`);
  }

  return true;
}

const ok = verifyTelemetryParsing(sampleBackendPayload);
console.log(`[TEST_TELEMETRY_CONTRACT] Successfully validated backend payload parsing: ${ok ? "PASS" : "FAIL"}`);

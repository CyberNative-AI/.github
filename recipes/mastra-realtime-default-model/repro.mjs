import { WebSocketServer } from 'ws';
import { OpenAIRealtimeVoice } from '@mastra/voice-openai-realtime';

const wss = new WebSocketServer({ port: 0 });
wss.on('connection', (_socket, req) => {
  console.log('requested model:', new URL(req.url, 'ws://localhost').searchParams.get('model'));
  process.exit(0);
});
const voice = new OpenAIRealtimeVoice({
  apiKey: 'unused',
  url: `ws://127.0.0.1:${wss.address().port}/v1/realtime`,
});
voice.connect().catch(() => {});

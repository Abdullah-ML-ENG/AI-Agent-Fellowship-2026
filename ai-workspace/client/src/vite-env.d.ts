/// <reference types="vite/client" />

interface SpeechRecognitionResultItem {
  transcript: string;
}

interface SpeechRecognitionResult {
  [index: number]: SpeechRecognitionResultItem;
}

interface SpeechRecognitionEvent extends Event {
  results: {
    [index: number]: SpeechRecognitionResult;
  };
}

interface SpeechRecognition extends EventTarget {
  lang: string;
  interimResults: boolean;
  maxAlternatives: number;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  start: () => void;
}

interface Window {
  SpeechRecognition?: new () => SpeechRecognition;
  webkitSpeechRecognition?: new () => SpeechRecognition;
}

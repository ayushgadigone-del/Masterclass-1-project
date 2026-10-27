"use client";
import { useCallback, useEffect, useRef, useState } from "react";

interface Props {
  onTranscript: (text: string) => void;
  language: "en" | "hi";
}

// Web Speech API — not in standard TS lib, type as any
declare global {
  interface Window {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    SpeechRecognition: any;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    webkitSpeechRecognition: any;
  }
}

export function VoiceRecorder({ onTranscript, language }: Props) {
  const [listening, setListening] = useState(false);
  const [interim, setInterim] = useState("");
  const [supported, setSupported] = useState(true);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    const SpeechRecognition =
      typeof window !== "undefined"
        ? window.SpeechRecognition ?? window.webkitSpeechRecognition
        : null;
    if (!SpeechRecognition) {
      setSupported(false);
      return;
    }
    const rec = new SpeechRecognition();
    rec.continuous = true;
    rec.interimResults = true;
    rec.maxAlternatives = 1;
    rec.lang = language === "hi" ? "hi-IN" : "en-IN";

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    rec.onresult = (e: any) => {
      let finalText = "";
      let interimText = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const t = e.results[i][0].transcript;
        if (e.results[i].isFinal) finalText += t + " ";
        else interimText += t;
      }
      setInterim(interimText);
      if (finalText.trim()) {
        onTranscript(finalText.trim());
        setInterim("");
      }
    };

    rec.onerror = () => setListening(false);
    rec.onend = () => setListening(false);
    recognitionRef.current = rec;
  }, [language, onTranscript]);

  const toggle = useCallback(() => {
    const rec = recognitionRef.current;
    if (!rec) return;
    if (listening) {
      rec.stop();
      setListening(false);
    } else {
      rec.lang = language === "hi" ? "hi-IN" : "en-IN";
      rec.start();
      setListening(true);
    }
  }, [listening, language]);

  if (!supported) {
    return (
      <p className="text-xs text-slate-400 italic">
        Voice input not supported in this browser. Please use text input.
      </p>
    );
  }

  return (
    <div className="flex flex-col items-center gap-2">
      <button
        type="button"
        onClick={toggle}
        aria-label={listening ? "Stop recording" : "Start voice input"}
        className={`
          relative w-16 h-16 rounded-full flex items-center justify-center
          transition-all duration-200 focus-visible:ring-4
          ${listening
            ? "bg-red-500 text-white shadow-lg shadow-red-200 scale-110 focus-visible:ring-red-300"
            : "bg-blue-600 text-white hover:bg-blue-700 focus-visible:ring-blue-300"
          }
        `}
      >
        {/* Pulse ring when listening */}
        {listening && (
          <span className="absolute inset-0 rounded-full bg-red-400 opacity-50 animate-ping" aria-hidden />
        )}
        <MicIcon className="w-7 h-7 relative" />
      </button>

      <span className="text-xs text-slate-500">
        {listening ? "Listening… speak now" : `Tap to speak (${language === "hi" ? "हिन्दी" : "English"})`}
      </span>

      {interim && (
        <p className="text-xs text-slate-400 italic max-w-xs text-center">
          &ldquo;{interim}&rdquo;
        </p>
      )}
    </div>
  );
}

function MicIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24" aria-hidden>
      <path d="M12 1a4 4 0 014 4v6a4 4 0 01-8 0V5a4 4 0 014-4zm0 2a2 2 0 00-2 2v6a2 2 0 004 0V5a2 2 0 00-2-2zm-7 8a1 1 0 012 0 5 5 0 0010 0 1 1 0 012 0 7 7 0 01-6 6.92V20h2a1 1 0 010 2H9a1 1 0 010-2h2v-2.08A7 7 0 015 11z"/>
    </svg>
  );
}

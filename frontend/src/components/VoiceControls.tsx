import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Volume2, VolumeX } from 'lucide-react';
import { Button } from '@/components/ui/button';

// Add type definitions for Web Speech API
declare global {
  interface Window {
    webkitSpeechRecognition: new () => SpeechRecognition;
  }
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start: () => void;
  stop: () => void;
  onresult: (event: SpeechRecognitionEvent) => void;
  onerror: (event: SpeechRecognitionError) => void;
  onend: () => void;
  maxAlternatives: number;
}

interface SpeechRecognitionEvent {
  results: SpeechRecognitionResultList;
}

interface SpeechRecognitionResultList {
  length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
  isFinal: boolean;
  length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

interface SpeechRecognitionError extends Event {
  error: string;
  message: string;
}

interface VoiceControlsProps {
  onSpeechResult: (text: string) => void;
  textToSpeak?: string;
  disabled?: boolean;
}

const VoiceControls: React.FC<VoiceControlsProps> = ({
  onSpeechResult,
  textToSpeak,
  disabled = false
}) => {
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const synthesisRef = useRef<SpeechSynthesis | null>(null);
  const finalTranscriptRef = useRef<string>('');

  useEffect(() => {
    // Initialize speech recognition
    if ('webkitSpeechRecognition' in window) {
      const SpeechRecognition = window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = 'en-US';
      recognitionRef.current.maxAlternatives = 1;

      recognitionRef.current.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
            finalTranscriptRef.current = finalTranscript;
            onSpeechResult(finalTranscript);
          } else {
            interimTranscript += transcript;
          }
        }
      };

      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
        // Restart recognition if it was stopped due to an error
        if (event.error === 'no-speech' || event.error === 'audio-capture') {
          setTimeout(() => {
            if (recognitionRef.current) {
              recognitionRef.current.start();
            }
          }, 1000);
        }
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
        // Restart recognition if it was stopped unexpectedly
        if (recognitionRef.current && isListening) {
          setTimeout(() => {
            if (recognitionRef.current) {
              recognitionRef.current.start();
            }
          }, 1000);
        }
      };
    }

    // Initialize speech synthesis
    synthesisRef.current = window.speechSynthesis;

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      if (synthesisRef.current) {
        synthesisRef.current.cancel();
      }
    };
  }, [onSpeechResult, isListening]);

  useEffect(() => {
    if (textToSpeak && !isSpeaking) {
      speakText(textToSpeak);
    }
  }, [textToSpeak]);

  const toggleListening = () => {
    if (!recognitionRef.current) return;

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      finalTranscriptRef.current = '';
      recognitionRef.current.start();
      setIsListening(true);
    }
  };

  const speakText = (text: string) => {
    if (!synthesisRef.current || !text) return;

    setIsSpeaking(true);
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    utterance.onend = () => {
      setIsSpeaking(false);
    };

    synthesisRef.current.speak(utterance);
  };

  const stopSpeaking = () => {
    if (synthesisRef.current) {
      synthesisRef.current.cancel();
      setIsSpeaking(false);
    }
  };

  return (
    <div className="flex items-center gap-2">
      <Button
        variant="outline"
        size="icon"
        onClick={toggleListening}
        disabled={disabled || !('webkitSpeechRecognition' in window)}
        className={isListening ? 'bg-red-100 hover:bg-red-200' : ''}
      >
        {isListening ? (
          <MicOff className="h-4 w-4 text-red-500" />
        ) : (
          <Mic className="h-4 w-4" />
        )}
      </Button>
      {textToSpeak && (
        <Button
          variant="outline"
          size="icon"
          onClick={isSpeaking ? stopSpeaking : () => speakText(textToSpeak)}
          disabled={disabled || !('speechSynthesis' in window)}
        >
          {isSpeaking ? (
            <VolumeX className="h-4 w-4" />
          ) : (
            <Volume2 className="h-4 w-4" />
          )}
        </Button>
      )}
    </div>
  );
};

export default VoiceControls; 
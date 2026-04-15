/**
 * Voice Input Component for Mobile Chat
 * 
- Speech recognition for voice commands
- Visual feedback during recording
- Integration with AI chat
 */

'use client';

import { useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, Square, Loader2 } from 'lucide-react';

interface VoiceInputProps {
  onTranscript: (text: string) => void;
  onError?: (error: string) => void;
  disabled?: boolean;
}

export default function VoiceInput({ onTranscript, onError, disabled }: VoiceInputProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [volume, setVolume] = useState(0);
  
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Start voice recording
  const startRecording = useCallback(async () => {
    try {
      // Check for Speech Recognition API support
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      
      if (!SpeechRecognition) {
        onError?.('Speech recognition is not supported in this browser');
        return;
      }

      // Initialize speech recognition
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      let finalTranscript = '';

      recognition.onresult = (event: SpeechRecognitionEvent) => {
        let interimTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }
      };

      recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
        console.error('Speech recognition error:', event.error);
        if (event.error !== 'no-speech') {
          onError?.(`Error: ${event.error}`);
        }
        stopRecording();
      };

      recognition.onend = () => {
        if (finalTranscript) {
          setIsProcessing(true);
          // Small delay to show processing state
          setTimeout(() => {
            onTranscript(finalTranscript);
            setIsProcessing(false);
          }, 500);
        }
      };

      // Start recording
      recognition.start();
      recognitionRef.current = recognition;

      // Get microphone access for visualizer
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Set up audio context for volume visualization
      const audioContext = new AudioContext();
      const analyser = audioContext.createAnalyser();
      const source = audioContext.createMediaStreamSource(stream);
      source.connect(analyser);
      
      analyser.fftSize = 256;
      audioContextRef.current = audioContext;
      analyserRef.current = analyser;

      // Start volume visualization
      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      const updateVolume = () => {
        if (!analyserRef.current) return;
        
        analyserRef.current.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
        setVolume(average / 128); // Normalize to 0-1
        
        animationFrameRef.current = requestAnimationFrame(updateVolume);
      };
      updateVolume();

      // Start duration timer
      setRecordingDuration(0);
      timerRef.current = setInterval(() => {
        setRecordingDuration(prev => prev + 1);
      }, 1000);

      setIsRecording(true);

    } catch (error) {
      console.error('Error starting recording:', error);
      onError?.('Could not access microphone. Please check permissions.');
    }
  }, [onTranscript, onError]);

  // Stop voice recording
  const stopRecording = useCallback(() => {
    // Stop speech recognition
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }

    // Stop audio context
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    // Cancel animation frame
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    // Clear timer
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }

    setIsRecording(false);
    setVolume(0);
    setRecordingDuration(0);
  }, []);

  // Toggle recording
  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  // Format duration
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="relative">
      <AnimatePresence>
        {isRecording && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            className="absolute bottom-full mb-4 left-1/2 -translate-x-1/2 bg-slate-800 rounded-2xl p-4 border border-slate-700 shadow-xl whitespace-nowrap z-50"
          >
            {/* Recording Visualizer */}
            <div className="flex items-center gap-3">
              {/* Animated bars */}
              <div className="flex items-end gap-0.5 h-8">
                {[...Array(8)].map((_, i) => (
                  <motion.div
                    key={i}
                    className="w-1 bg-red-500 rounded-full"
                    animate={{
                      height: volume > 0 
                        ? [4, Math.max(4, volume * 32), 4]
                        : [4, 12, 4],
                    }}
                    transition={{
                      duration: 0.3,
                      repeat: Infinity,
                      delay: i * 0.05,
                      ease: "easeInOut",
                    }}
                  />
                ))}
              </div>

              {/* Recording info */}
              <div className="flex flex-col">
                <span className="text-white font-medium text-sm">Listening...</span>
                <span className="text-slate-400 text-xs">{formatDuration(recordingDuration)}</span>
              </div>

              {/* Stop button */}
              <button
                type="button"
                onClick={stopRecording}
                aria-label="Stop voice recording"
                title="Stop voice recording"
                className="p-2 bg-red-500/20 hover:bg-red-500/30 rounded-lg transition-colors"
              >
                <Square className="w-4 h-4 text-red-500" fill="currentColor" />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main button */}
      <motion.button
        type="button"
        onClick={toggleRecording}
        disabled={disabled || isProcessing}
        aria-label={isRecording ? "Stop voice input" : "Start voice input"}
        title={isRecording ? "Stop voice input" : "Start voice input"}
        whileTap={{ scale: 0.9 }}
        className={`relative p-3 rounded-xl transition-all ${
          isRecording
            ? 'bg-red-500/20 text-red-500'
            : 'bg-blue-600/20 text-blue-400 hover:bg-blue-600/30'
        } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        {isProcessing ? (
          <Loader2 className="w-5 h-5 animate-spin" />
        ) : (
          <Mic className="w-5 h-5" />
        )}

        {/* Ripple effect when recording */}
        {isRecording && (
          <>
            <motion.span
              className="absolute inset-0 rounded-xl bg-red-500/30"
              animate={{ scale: [1, 1.5], opacity: [0.5, 0] }}
              transition={{ duration: 1, repeat: Infinity }}
            />
            <motion.span
              className="absolute inset-0 rounded-xl bg-red-500/30"
              animate={{ scale: [1, 1.5], opacity: [0.5, 0] }}
              transition={{ duration: 1, repeat: Infinity, delay: 0.5 }}
            />
          </>
        )}
      </motion.button>
    </div>
  );
}

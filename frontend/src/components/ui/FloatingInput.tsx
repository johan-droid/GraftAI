"use client";

import { useState, forwardRef } from "react";
import { Box, TextField, TextFieldProps, InputAdornment } from "@mui/material";
import { motion, AnimatePresence } from "framer-motion";
import { Eye, EyeOff, LucideIcon } from "lucide-react";

interface FloatingInputProps extends Omit<TextFieldProps, "variant"> {
  icon?: LucideIcon;
  errorMessage?: string;
  isPassword?: boolean;
}

export const FloatingInput = forwardRef<HTMLInputElement, FloatingInputProps>(
  ({ icon: Icon, errorMessage, isPassword, type, ...props }, ref) => {
    const [isFocused, setIsFocused] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const hasValue = Boolean(props.value || props.defaultValue);

    const inputType = isPassword ? (showPassword ? "text" : "password") : type;

    return (
      <Box sx={{ position: "relative", width: "100%" }}>
        <TextField
          {...props}
          inputRef={ref}
          type={inputType}
          fullWidth
          onFocus={(e) => {
            setIsFocused(true);
            props.onFocus?.(e);
          }}
          onBlur={(e) => {
            setIsFocused(false);
            props.onBlur?.(e);
          }}
          sx={{
            "& .MuiOutlinedInput-root": {
              background: "rgba(255, 255, 255, 0.02)",
              borderRadius: "0",
              border: "1px dashed",
              borderColor: errorMessage
                ? "var(--accent)"
                : isFocused
                ? "var(--primary)"
                : "var(--border-subtle)",
              color: "var(--text-primary)",
              transition: "all 0.2s ease",
              boxShadow: isFocused ? "0 0 10px rgba(0, 255, 156, 0.1)" : "none",
              "&:hover": {
                borderColor: errorMessage
                  ? "var(--accent)"
                  : "var(--primary)",
              },
              "&.Mui-focused": {
                borderColor: errorMessage
                  ? "var(--accent)"
                  : "var(--primary)",
              },
            },
            "& .MuiOutlinedInput-notchedOutline": {
              border: "none",
            },
            "& .MuiInputBase-input": {
              py: 2,
              px: Icon ? 1.5 : 2,
              fontSize: "12px",
              fontFamily: "var(--font-mono)",
              "&::placeholder": {
                color: "var(--text-faint)",
                opacity: 0.5,
                textTransform: "uppercase",
              },
            },
            ...props.sx,
          }}
          InputProps={{
            ...props.InputProps,
            startAdornment: Icon ? (
              <InputAdornment position="start">
                <Icon
                  size={16}
                  style={{
                    color: errorMessage
                      ? "var(--accent)"
                      : isFocused
                      ? "var(--primary)"
                      : "var(--text-muted)",
                    transition: "color 0.2s ease",
                  }}
                />
              </InputAdornment>
            ) : null,
            endAdornment: isPassword ? (
              <InputAdornment position="end">
                <Box
                  component="button"
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  sx={{
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                    p: 0.5,
                    color: "var(--text-muted)",
                    "&:hover": { color: "var(--primary)" },
                    transition: "color 0.2s",
                  }}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </Box>
              </InputAdornment>
            ) : null,
          }}
        />

        {/* Error Message */}
        <AnimatePresence>
          {errorMessage && (
            <motion.div
              initial={{ opacity: 0, y: -10, height: 0 }}
              animate={{ opacity: 1, y: 0, height: "auto" }}
              exit={{ opacity: 0, y: -10, height: 0 }}
              transition={{ duration: 0.2 }}
            >
              <Box
                sx={{
                  mt: 1,
                  fontSize: "9px",
                  color: "var(--accent)",
                  fontFamily: "var(--font-mono)",
                  textTransform: "uppercase",
                  display: "flex",
                  alignItems: "center",
                  gap: 0.5,
                }}
              >
                ERR_INPUT: {errorMessage}
              </Box>
            </motion.div>
          )}
        </AnimatePresence>
      </Box>
    );
  }
);

FloatingInput.displayName = "FloatingInput";

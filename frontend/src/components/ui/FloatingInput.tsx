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
          ref={ref}
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
              background: "hsl(240, 24%, 14%)",
              borderRadius: "12px",
              border: "1px solid",
              borderColor: errorMessage
                ? "hsla(346, 84%, 61%, 0.5)"
                : isFocused
                ? "hsla(239, 84%, 67%, 0.6)"
                : "hsla(239, 84%, 67%, 0.15)",
              color: "hsl(220, 20%, 98%)",
              transition: "all 0.2s ease",
              boxShadow: isFocused ? "0 0 0 3px hsla(239, 84%, 67%, 0.15)" : "none",
              "&:hover": {
                borderColor: errorMessage
                  ? "hsla(346, 84%, 61%, 0.6)"
                  : "hsla(239, 84%, 67%, 0.3)",
              },
              "&.Mui-focused": {
                borderColor: errorMessage
                  ? "hsla(346, 84%, 61%, 0.7)"
                  : "hsla(239, 84%, 67%, 0.8)",
                boxShadow: errorMessage
                  ? "0 0 0 3px hsla(346, 84%, 61%, 0.15)"
                  : "0 0 0 3px hsla(239, 84%, 67%, 0.2)",
              },
            },
            "& .MuiOutlinedInput-notchedOutline": {
              border: "none",
            },
            "& .MuiInputBase-input": {
              py: 2,
              px: Icon ? 1.5 : 2,
              fontSize: "0.9375rem",
              "&::placeholder": {
                color: "hsl(215, 16%, 35%)",
                opacity: 1,
              },
            },
            ...props.sx,
          }}
          InputProps={{
            ...props.InputProps,
            startAdornment: Icon ? (
              <InputAdornment position="start">
                <Icon
                  size={20}
                  style={{
                    color: errorMessage
                      ? "hsl(346, 84%, 61%)"
                      : isFocused
                      ? "hsl(239, 84%, 67%)"
                      : "hsl(215, 16%, 40%)",
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
                    color: "hsl(215, 16%, 40%)",
                    "&:hover": { color: "hsl(215, 16%, 70%)" },
                    transition: "color 0.2s",
                  }}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
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
                  fontSize: "0.8125rem",
                  color: "hsl(346, 84%, 61%)",
                  display: "flex",
                  alignItems: "center",
                  gap: 0.5,
                }}
              >
                {errorMessage}
              </Box>
            </motion.div>
          )}
        </AnimatePresence>
      </Box>
    );
  }
);

FloatingInput.displayName = "FloatingInput";

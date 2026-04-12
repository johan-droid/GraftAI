"use client";

import { ReactNode } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Box,
  Typography,
} from "@mui/material";
import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  actions?: ReactNode;
  maxWidth?: "xs" | "sm" | "md" | "lg" | "xl";
  fullWidth?: boolean;
}

export function Modal({
  open,
  onClose,
  title,
  children,
  actions,
  maxWidth = "sm",
  fullWidth = true,
}: ModalProps) {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth={maxWidth}
      fullWidth={fullWidth}
      PaperProps={{
        sx: {
          background: "linear-gradient(135deg, hsl(240, 24%, 14%) 0%, hsl(240, 24%, 10%) 100%)",
          border: "1px solid hsla(239, 84%, 67%, 0.2)",
          borderRadius: "16px",
          boxShadow: "0 25px 50px -12px rgba(0,0,0,0.5)",
          overflow: "hidden",
        },
      }}
      sx={{
        "& .MuiBackdrop-root": {
          background: "hsla(240, 24%, 7%, 0.8)",
          backdropFilter: "blur(4px)",
        },
      }}
    >
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
          >
            {title && (
              <DialogTitle
                sx={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  p: 3,
                  borderBottom: "1px solid hsla(239, 84%, 67%, 0.1)",
                }}
              >
                <Typography
                  variant="h6"
                  sx={{
                    fontWeight: 700,
                    color: "hsl(220, 20%, 98%)",
                    letterSpacing: "-0.01em",
                  }}
                >
                  {title}
                </Typography>
                <IconButton
                  onClick={onClose}
                  sx={{
                    color: "hsl(215, 16%, 55%)",
                    "&:hover": {
                      color: "hsl(220, 20%, 98%)",
                      background: "hsla(239, 84%, 67%, 0.1)",
                    },
                  }}
                >
                  <X size={20} />
                </IconButton>
              </DialogTitle>
            )}

            <DialogContent sx={{ p: 3 }}>{children}</DialogContent>

            {actions && (
              <DialogActions
                sx={{
                  p: 3,
                  borderTop: "1px solid hsla(239, 84%, 67%, 0.1)",
                  gap: 2,
                }}
              >
                {actions}
              </DialogActions>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </Dialog>
  );
}

// Confirmation modal preset
interface ConfirmModalProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  confirmVariant?: "danger" | "primary";
  loading?: boolean;
}

export function ConfirmModal({
  open,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = "Confirm",
  cancelText = "Cancel",
  confirmVariant = "primary",
  loading = false,
}: ConfirmModalProps) {
  const isDanger = confirmVariant === "danger";

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={title}
      maxWidth="xs"
      actions={
        <>
          <Box
            component="button"
            onClick={onClose}
            disabled={loading}
            sx={{
              px: 3,
              py: 1.5,
              borderRadius: "12px",
              border: "1px solid hsla(239, 84%, 67%, 0.3)",
              background: "transparent",
              color: "hsl(220, 20%, 98%)",
              fontWeight: 600,
              fontSize: "0.9375rem",
              cursor: "pointer",
              transition: "all 0.2s",
              "&:hover": {
                background: "hsla(239, 84%, 67%, 0.1)",
                borderColor: "hsla(239, 84%, 67%, 0.5)",
              },
              "&:disabled": {
                opacity: 0.5,
                cursor: "not-allowed",
              },
            }}
          >
            {cancelText}
          </Box>
          <Box
            component="button"
            onClick={onConfirm}
            disabled={loading}
            sx={{
              px: 3,
              py: 1.5,
              borderRadius: "12px",
              border: "none",
              background: isDanger
                ? "hsl(346, 84%, 61%)"
                : "linear-gradient(135deg, hsl(239, 84%, 67%) 0%, hsl(330, 81%, 60%) 100%)",
              color: "white",
              fontWeight: 600,
              fontSize: "0.9375rem",
              cursor: "pointer",
              transition: "all 0.2s",
              "&:hover": {
                background: isDanger
                  ? "hsl(346, 84%, 51%)"
                  : "linear-gradient(135deg, hsl(239, 84%, 57%) 0%, hsl(330, 81%, 50%) 100%)",
                transform: "translateY(-1px)",
              },
              "&:disabled": {
                opacity: 0.5,
                cursor: "not-allowed",
              },
            }}
          >
            {loading ? "Processing..." : confirmText}
          </Box>
        </>
      }
    >
      <Typography sx={{ color: "hsl(215, 16%, 70%)", lineHeight: 1.6 }}>
        {message}
      </Typography>
    </Modal>
  );
}

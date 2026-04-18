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
import { alpha } from "@mui/material/styles";

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
          backgroundColor: "#FFFFFF",
          border: "1px solid #DADCE0",
          borderRadius: "28px",
          boxShadow: "0 24px 60px -36px rgba(32,33,36,0.35)",
          overflow: "hidden",
        },
      }}
      sx={{
        "& .MuiBackdrop-root": {
          backgroundColor: alpha("#3C4043", 0.32),
          backdropFilter: "blur(3px)",
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
                  px: 3,
                  py: 2.5,
                  borderBottom: "1px solid #DADCE0",
                }}
              >
                <Typography
                  variant="h6"
                  sx={{
                    fontWeight: 700,
                    color: "#202124",
                    letterSpacing: "-0.01em",
                  }}
                >
                  {title}
                </Typography>
                <IconButton
                  onClick={onClose}
                  sx={{
                    color: "#5F6368",
                    border: "1px solid #DADCE0",
                    borderRadius: "12px",
                    "&:hover": {
                      color: "#202124",
                      background: "#F1F3F4",
                    },
                  }}
                >
                  <X size={20} />
                </IconButton>
              </DialogTitle>
            )}

            <DialogContent sx={{ px: 3, py: 2.5 }}>{children}</DialogContent>

            {actions && (
              <DialogActions
                sx={{
                  px: 3,
                  py: 2.5,
                  borderTop: "1px solid #DADCE0",
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
              border: "1px solid #DADCE0",
              background: "#FFFFFF",
              color: "#202124",
              fontWeight: 600,
              fontSize: "0.9375rem",
              cursor: "pointer",
              transition: "all 0.2s",
              "&:hover": {
                background: "#F1F3F4",
                borderColor: "#BDC1C6",
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
              background: isDanger ? "#D93025" : "#1A73E8",
              color: "white",
              fontWeight: 600,
              fontSize: "0.9375rem",
              cursor: "pointer",
              transition: "all 0.2s",
              "&:hover": {
                background: isDanger ? "#B3261E" : "#1558B0",
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
      <Typography sx={{ color: "#5F6368", lineHeight: 1.6 }}>
        {message}
      </Typography>
    </Modal>
  );
}

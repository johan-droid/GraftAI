'use client';

import { useState } from 'react';
import { Box, Button, Container, Typography, TextField, Card, CardContent, Divider, IconButton, InputAdornment, Checkbox, FormControlLabel } from '@mui/material';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Eye, EyeOff, Mail, Lock, User, ArrowRight, Check } from 'lucide-react';
import GitHubIcon from '@mui/icons-material/GitHub';
import GoogleIcon from '@mui/icons-material/Google';
import { useAuthContext } from '@/providers/auth-provider';

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuthContext();
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [agreedToTerms, setAgreedToTerms] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    if (!formData.name.trim()) {
      newErrors.name = 'Full name is required';
    }
    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email';
    }
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }
    if (!agreedToTerms) {
      newErrors.terms = 'You must agree to the terms and conditions';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    setIsLoading(true);
    try {
      const result = await register(formData.name, formData.email, formData.password);
      if (result.error) {
        setErrors({ submit: result.error.message });
      } else {
        router.push('/dashboard');
      }
    } catch (error) {
      setErrors({ submit: 'An unexpected error occurred. Please try again.' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSocialLogin = async (provider: string) => {
    window.location.href = `/api/auth/oauth/${provider}`;
  };

  return (
    <Box sx={{ minHeight: '100vh', background: 'linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #0f0f1a 100%)', display: 'flex', alignItems: 'center', py: 4 }}>
      <Container maxWidth="sm">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <Card sx={{ background: 'linear-gradient(135deg, rgba(26, 26, 46, 0.95) 0%, rgba(15, 15, 26, 0.98) 100%)', backdropFilter: 'blur(20px)', border: '1px solid rgba(99, 102, 241, 0.2)', boxShadow: '0 25px 50px rgba(0, 0, 0, 0.5)' }}>
            <CardContent sx={{ p: { xs: 3, md: 5 } }}>
              {/* Header */}
              <Box textAlign="center" mb={4}>
                <Typography variant="h4" sx={{ fontWeight: 700, mb: 1, background: 'linear-gradient(135deg, #6366f1 0%, #ec4899 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                  Create Account
                </Typography>
                <Typography variant="body2" sx={{ color: '#94a3b8' }}>
                  Start your 14-day free trial today
                </Typography>
              </Box>

              {/* Social Login */}
              <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
                <Button
                  fullWidth
                  variant="outlined"
                  onClick={() => handleSocialLogin('google')}
                  startIcon={<GoogleIcon />}
                  sx={{ py: 1.5, borderColor: 'rgba(99, 102, 241, 0.3)', '&:hover': { borderColor: 'rgba(99, 102, 241, 0.5)', background: 'rgba(99, 102, 241, 0.05)' } }}
                >
                  Google
                </Button>
                <Button
                  fullWidth
                  variant="outlined"
                  onClick={() => handleSocialLogin('github')}
                  startIcon={<GitHubIcon />}
                  sx={{ py: 1.5, borderColor: 'rgba(99, 102, 241, 0.3)', '&:hover': { borderColor: 'rgba(99, 102, 241, 0.5)', background: 'rgba(99, 102, 241, 0.05)' } }}
                >
                  GitHub
                </Button>
              </Box>

              <Divider sx={{ my: 3, borderColor: 'rgba(148, 163, 184, 0.1)' }}>
                <Typography variant="caption" sx={{ color: '#64748b', px: 2 }}>
                  OR
                </Typography>
              </Divider>

              {/* Form */}
              <form onSubmit={handleSubmit}>
                <TextField
                  fullWidth
                  label="Full Name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  error={!!errors.name}
                  helperText={errors.name}
                  sx={{ mb: 2.5 }}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <User size={18} color="#64748b" />
                      </InputAdornment>
                    ),
                  }}
                />

                <TextField
                  fullWidth
                  label="Email Address"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  error={!!errors.email}
                  helperText={errors.email}
                  sx={{ mb: 2.5 }}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <Mail size={18} color="#64748b" />
                      </InputAdornment>
                    ),
                  }}
                />

                <TextField
                  fullWidth
                  label="Password"
                  type={showPassword ? 'text' : 'password'}
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  error={!!errors.password}
                  helperText={errors.password}
                  sx={{ mb: 2 }}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <Lock size={18} color="#64748b" />
                      </InputAdornment>
                    ),
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton onClick={() => setShowPassword(!showPassword)} edge="end">
                          {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                />

                <Box sx={{ mb: 3 }}>
                  {[
                    'At least 8 characters',
                    'Contains uppercase & lowercase',
                    'Contains a number or special character',
                  ].map((req, i) => (
                    <Box key={i} sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
                      <Check size={14} color={formData.password.length >= 8 ? '#10b981' : '#64748b'} />
                      <Typography variant="caption" sx={{ color: formData.password.length >= 8 ? '#10b981' : '#64748b' }}>
                        {req}
                      </Typography>
                    </Box>
                  ))}
                </Box>

                <FormControlLabel
                  control={
                    <Checkbox
                      checked={agreedToTerms}
                      onChange={(e) => setAgreedToTerms(e.target.checked)}
                      sx={{ color: errors.terms ? '#ef4444' : undefined }}
                    />
                  }
                  label={
                    <Typography variant="body2" sx={{ color: '#94a3b8' }}>
                      I agree to the{' '}
                      <Link href="/terms" style={{ color: '#6366f1', textDecoration: 'none' }}>
                        Terms of Service
                      </Link>{' '}
                      and{' '}
                      <Link href="/privacy" style={{ color: '#6366f1', textDecoration: 'none' }}>
                        Privacy Policy
                      </Link>
                    </Typography>
                  }
                  sx={{ mb: 2 }}
                />
                {errors.terms && (
                  <Typography color="error" variant="caption" sx={{ display: 'block', mb: 2 }}>
                    {errors.terms}
                  </Typography>
                )}

                {errors.submit && (
                  <Typography color="error" variant="body2" sx={{ mb: 2, textAlign: 'center' }}>
                    {errors.submit}
                  </Typography>
                )}

                <Button
                  type="submit"
                  fullWidth
                  variant="contained"
                  disabled={isLoading}
                  sx={{ py: 1.5, fontSize: '1rem', borderRadius: '10px' }}
                >
                  {isLoading ? 'Creating account...' : 'Create Account'}
                  {!isLoading && <ArrowRight size={18} style={{ marginLeft: 8 }} />}
                </Button>
              </form>

              {/* Footer */}
              <Box textAlign="center" mt={4}>
                <Typography variant="body2" sx={{ color: '#64748b' }}>
                  Already have an account?{' '}
                  <Link href="/login" style={{ color: '#6366f1', textDecoration: 'none', fontWeight: 600 }}>
                    Sign in
                  </Link>
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </motion.div>
      </Container>
    </Box>
  );
}

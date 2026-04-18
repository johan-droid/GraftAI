type OAuthCredentialPair = {
  clientId?: string;
  clientSecret?: string;
};

function resolveFirstEnvValue(...names: string[]): string | undefined {
  for (const name of names) {
    const value = process.env[name]?.trim();
    if (value) {
      return value;
    }
  }

  return undefined;
}

export function getGoogleOAuthCredentials(): OAuthCredentialPair {
  return {
    clientId: resolveFirstEnvValue("GOOGLE_CLIENT_ID", "AUTH_GOOGLE_ID"),
    clientSecret: resolveFirstEnvValue("GOOGLE_CLIENT_SECRET", "AUTH_GOOGLE_SECRET"),
  };
}

export function getMicrosoftOAuthCredentials(): OAuthCredentialPair {
  return {
    clientId: resolveFirstEnvValue("MICROSOFT_CLIENT_ID", "AUTH_MICROSOFT_ENTRA_ID_ID"),
    clientSecret: resolveFirstEnvValue("MICROSOFT_CLIENT_SECRET", "AUTH_MICROSOFT_ENTRA_ID_SECRET"),
  };
}

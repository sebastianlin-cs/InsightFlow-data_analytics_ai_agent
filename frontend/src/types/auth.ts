export type User = {
  id: number;
  email: string;
  is_active: boolean;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
};

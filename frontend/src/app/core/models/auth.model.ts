export type LoginRequest = { username: string; password: string };
export type LoginResponse = { access: string; refresh: string };

export type RegisterRequest = {
  username: string;
  email?: string | null;          
  password: string;               
};

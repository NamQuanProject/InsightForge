/**
 * TypeScript types for the InsightForge application
 */

export interface Report {
  id: string;
  title: string;
  description: string;
  createdAt: Date;
  updatedAt: Date;
  status: 'draft' | 'pending' | 'approved' | 'rejected';
  generatedBy: string;
}

export interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'user' | 'viewer';
}

export interface DataSource {
  id: string;
  name: string;
  type: string;
  connectionString: string;
  isActive: boolean;
}
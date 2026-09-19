export type FieldType = 'text' | 'textarea' | 'number' | 'currency' | 'date' | 'email' | 'phone' | 'select' | 'radio' | 'checkbox' | 'file';

export interface FieldSource {
  page: number;
  original_label: string;
  section: string;
  confidence: 'high' | 'medium' | 'low';
  excerpt?: string;
}

export interface ValidationRule {
  type: string;
  value?: any;
  message: string;
}

export interface FormField {
  id: string;
  section_id: string;
  label: string;
  type: FieldType;
  required: boolean;
  placeholder?: string;
  options?: string[];
  validation?: ValidationRule[];
  source?: FieldSource;
  default_value?: any;
  help_text?: string;
}

export interface FormSection {
  id: string;
  title: string;
  description?: string;
  fields: FormField[];
  order: number;
  icon?: string;
}

export interface RequiredDocument {
  id: string;
  name: string;
  description: string;
  required: boolean;
  accepted_formats: string[];
  max_size_mb: number;
  extractable_fields?: string[];
}

export interface DocumentMetadata {
  source_type: string;
  original_filename?: string;
  page_count: number;
  file_size_bytes: number;
  mime_type?: string;
  extraction_method: string;
  is_demo: boolean;
}

export interface FormDocument {
  id: string;
  title: string;
  description: string;
  sections: FormSection[];
  required_documents: RequiredDocument[];
  metadata: DocumentMetadata;
}

export interface ValidationIssue {
  id: string;
  severity: 'info' | 'warning' | 'error';
  title: string;
  description: string;
  field_id?: string;
  document_ref?: string;
  suggested_action?: string;
  source?: string;
}

export interface CheckCategory {
  name: string;
  status: 'passed' | 'warning' | 'failed';
  detail: string;
}

export interface ApplicationCheckResult {
  overall_status: 'clean' | 'warning' | 'error';
  categories: CheckCategory[];
  issues: ValidationIssue[];
  completion_percentage: number;
  required_fields_complete: number;
  required_fields_total: number;
  documents_uploaded: number;
  documents_required: number;
}

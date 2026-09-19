import axios from 'axios';
import type { FormDocument, ValidationIssue, ApplicationCheckResult } from '../types/schema';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
});

export const analyzeDemo = async () => {
  const res = await api.post<{ session_id: string; form_document: FormDocument; mode: string }>('/analyze/demo');
  return res.data;
};

export const analyzeDocument = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const res = await api.post<{ session_id: string; form_document: FormDocument; mode: string }>('/analyze', formData);
  return res.data;
};

export const validateValues = async (formDoc: FormDocument, values: Record<string, any>, uploadedDocIds: string[] = []) => {
  const res = await api.post<{ issues: ValidationIssue[] }>('/validate', {
    form_document: formDoc,
    values,
    uploaded_document_ids: uploadedDocIds,
  });
  return res.data;
};

export const validateDemo = async (uploadedDocIds: string[] = []) => {
  const res = await api.post<{ issues: ValidationIssue[] }>('/validate/demo', {
    uploaded_document_ids: uploadedDocIds,
  });
  return res.data;
};

export const checkApplication = async (formDoc: FormDocument, values: Record<string, any>, uploadedDocIds: string[] = []) => {
  const res = await api.post<ApplicationCheckResult>('/check', {
    form_document: formDoc,
    values,
    uploaded_document_ids: uploadedDocIds,
  });
  return res.data;
};

export const checkApplicationDemo = async (uploadedDocIds: string[] = []) => {
  const res = await api.post<ApplicationCheckResult>('/check/demo', {
    uploaded_document_ids: uploadedDocIds,
  });
  return res.data;
};

export const exportPdf = async (formDoc: FormDocument, values: Record<string, any>, issues: ValidationIssue[], uploadedDocs: string[]) => {
  const res = await api.post('/export', {
    form_document: formDoc,
    values,
    issues,
    uploaded_documents: uploadedDocs,
  }, { responseType: 'blob' });
  return res.data;
};

export const exportDemoPdf = async (values: Record<string, any>, issues: ValidationIssue[], uploadedDocs: string[]) => {
  const res = await api.post('/export/demo', {
    values,
    issues,
    uploaded_documents: uploadedDocs,
  }, { responseType: 'blob' });
  return res.data;
};

export const uploadSupportingDocument = async (file: File, docId: string, isDemo: boolean = false) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('doc_id', docId);
  formData.append('is_demo', String(isDemo));
  const res = await api.post('/documents/upload', formData);
  return res.data;
};

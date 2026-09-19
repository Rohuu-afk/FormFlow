import { create } from 'zustand';
import type { FormDocument, ValidationIssue } from '../types/schema';

interface FormState {
  formDocument: FormDocument | null;
  values: Record<string, any>;
  issues: ValidationIssue[];
  uploadedDocuments: string[]; // array of doc_ids
  mode: 'real' | 'demo';
  
  setFormDocument: (doc: FormDocument, mode: 'real' | 'demo') => void;
  setValue: (fieldId: string, value: any) => void;
  setValues: (values: Record<string, any>) => void;
  setIssues: (issues: ValidationIssue[]) => void;
  addUploadedDocument: (docId: string) => void;
  reset: () => void;
}

export const useFormStore = create<FormState>((set) => ({
  formDocument: null,
  values: {},
  issues: [],
  uploadedDocuments: [],
  mode: 'real',

  setFormDocument: (doc, mode) => set({ formDocument: doc, mode, values: {}, issues: [], uploadedDocuments: [] }),
  setValue: (fieldId, value) => set((state) => ({ values: { ...state.values, [fieldId]: value } })),
  setValues: (values) => set({ values }),
  setIssues: (issues) => set({ issues }),
  addUploadedDocument: (docId) => set((state) => ({ 
    uploadedDocuments: state.uploadedDocuments.includes(docId) 
      ? state.uploadedDocuments 
      : [...state.uploadedDocuments, docId] 
  })),
  reset: () => set({ formDocument: null, values: {}, issues: [], uploadedDocuments: [], mode: 'real' }),
}));

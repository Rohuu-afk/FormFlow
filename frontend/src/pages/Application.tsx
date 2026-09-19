import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useFormStore } from '../store/useFormStore';
import { validateDemo, validateValues, checkApplicationDemo, checkApplication, uploadSupportingDocument, exportDemoPdf, exportPdf } from '../services/api';


export default function Application() {
  const navigate = useNavigate();
  const { formDocument, values, setValue, issues, setIssues, uploadedDocuments, addUploadedDocument, mode } = useFormStore();
  const [activeSection, setActiveSection] = useState(0);
  const [checking, setChecking] = useState(false);
  const [checkResult, setCheckResult] = useState<any>(null);

  useEffect(() => {
    if (!formDocument) {
      navigate('/');
    }
  }, [formDocument, navigate]);

  if (!formDocument) return null;

  const section = formDocument.sections[activeSection];

  const handleValidate = async () => {
    try {
      const res = mode === 'demo' 
        ? await validateDemo(uploadedDocuments)
        : await validateValues(formDocument, values, uploadedDocuments);
      setIssues(res.issues);
    } catch (e) {
      console.error(e);
    }
  };

  const handleCheck = async () => {
    setChecking(true);
    try {
      const res = mode === 'demo'
        ? await checkApplicationDemo(uploadedDocuments)
        : await checkApplication(formDocument, values, uploadedDocuments);
      setCheckResult(res);
      setIssues(res.issues);
    } catch (e) {
      console.error(e);
    } finally {
      setChecking(false);
    }
  };

  const handleExport = async () => {
    try {
      const blob = mode === 'demo'
        ? await exportDemoPdf(values, issues, uploadedDocuments)
        : await exportPdf(formDocument, values, issues, uploadedDocuments);
      
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'application_summary.pdf');
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
    } catch (e) {
      console.error(e);
    }
  };

  const handleDocUpload = async (e: React.ChangeEvent<HTMLInputElement>, docId: string) => {
    if (!e.target.files?.[0]) return;
    try {
      await uploadSupportingDocument(e.target.files[0], docId, mode === 'demo');
      addUploadedDocument(docId);
      handleValidate(); // Re-validate after doc upload
    } catch (e) {
      console.error(e);
    }
  };

  const getIssueForField = (fieldId: string) => issues.find(i => i.field_id === fieldId);

  return (
    <div className="min-h-screen bg-gray-100 p-4 md:p-8">
      <div className="max-w-6xl mx-auto bg-white shadow-lg rounded-xl overflow-hidden flex flex-col md:flex-row min-h-[80vh]">
        
        {/* Sidebar Navigation */}
        <div className="w-full md:w-64 bg-gray-50 border-r border-gray-200 p-4">
          <h2 className="font-bold text-lg mb-6 truncate" title={formDocument.title}>{formDocument.title}</h2>
          <div className="space-y-2">
            {formDocument.sections.map((sec, idx) => (
              <button
                key={sec.id}
                onClick={() => setActiveSection(idx)}
                className={`w-full text-left px-3 py-2 rounded-md text-sm font-medium transition-colors ${activeSection === idx ? 'bg-indigo-100 text-indigo-700' : 'text-gray-600 hover:bg-gray-100'}`}
              >
                {sec.icon} {sec.title}
              </button>
            ))}
            <button
               onClick={() => setActiveSection(-1)}
               className={`w-full text-left px-3 py-2 rounded-md text-sm font-medium transition-colors ${activeSection === -1 ? 'bg-indigo-100 text-indigo-700' : 'text-gray-600 hover:bg-gray-100'}`}
            >
              📁 Supporting Documents
            </button>
          </div>
          
          <div className="mt-8 pt-4 border-t border-gray-200 space-y-3">
             <button onClick={handleCheck} disabled={checking} className="w-full bg-gray-800 text-white px-4 py-2 rounded-md text-sm font-semibold hover:bg-gray-700 transition">
               {checking ? 'Checking...' : 'Check Application'}
             </button>
             {checkResult && (
               <button onClick={handleExport} className="w-full bg-indigo-600 text-white px-4 py-2 rounded-md text-sm font-semibold hover:bg-indigo-700 transition">
                 Export PDF
               </button>
             )}
          </div>
        </div>

        {/* Main Content Area */}
        <div className="flex-1 p-6 md:p-8 overflow-y-auto">
          {activeSection >= 0 ? (
            <div className="max-w-2xl">
              <div className="mb-8">
                <h3 className="text-2xl font-bold text-gray-900">{section.title}</h3>
                {section.description && <p className="text-gray-500 mt-1">{section.description}</p>}
              </div>

              <div className="space-y-6">
                {section.fields.map(field => {
                  const issue = getIssueForField(field.id);
                  return (
                    <div key={field.id} className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        {field.label} {field.required && <span className="text-red-500">*</span>}
                      </label>
                      {field.type === 'textarea' ? (
                        <textarea
                          className="w-full border-gray-300 rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border"
                          value={values[field.id] || ''}
                          onChange={(e) => setValue(field.id, e.target.value)}
                          onBlur={handleValidate}
                          placeholder={field.placeholder}
                        />
                      ) : field.type === 'select' ? (
                        <select
                          className="w-full border-gray-300 rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border"
                          value={values[field.id] || ''}
                          onChange={(e) => setValue(field.id, e.target.value)}
                          onBlur={handleValidate}
                        >
                          <option value="">Select...</option>
                          {field.options?.map(opt => <option key={opt} value={opt}>{opt}</option>)}
                        </select>
                      ) : field.type === 'radio' ? (
                         <div className="space-y-2">
                           {field.options?.map(opt => (
                             <label key={opt} className="inline-flex items-center mr-4">
                               <input type="radio" name={field.id} value={opt} checked={values[field.id] === opt} onChange={(e) => setValue(field.id, e.target.value)} onBlur={handleValidate} className="text-indigo-600 focus:ring-indigo-500" />
                               <span className="ml-2 text-sm text-gray-700">{opt}</span>
                             </label>
                           ))}
                         </div>
                      ) : field.type === 'checkbox' ? (
                        <label className="inline-flex items-center mt-2">
                           <input type="checkbox" checked={!!values[field.id]} onChange={(e) => setValue(field.id, e.target.checked)} onBlur={handleValidate} className="rounded text-indigo-600 focus:ring-indigo-500" />
                           <span className="ml-2 text-sm text-gray-700">{field.label}</span>
                        </label>
                      ) : (
                        <input
                          type={field.type === 'date' ? 'date' : 'text'}
                          className="w-full border-gray-300 rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border"
                          value={values[field.id] || ''}
                          onChange={(e) => setValue(field.id, e.target.value)}
                          onBlur={handleValidate}
                          placeholder={field.placeholder}
                        />
                      )}
                      
                      {field.help_text && <p className="mt-1 text-xs text-gray-500">{field.help_text}</p>}
                      
                      {issue && (
                        <div className={`mt-2 p-3 text-sm rounded-md ${issue.severity === 'error' ? 'bg-red-50 text-red-700 border border-red-200' : 'bg-yellow-50 text-yellow-700 border border-yellow-200'}`}>
                          <div className="font-semibold">{issue.title}</div>
                          <div>{issue.description}</div>
                          {issue.source && <div className="mt-1 text-xs opacity-80 italic">Source: {issue.source}</div>}
                        </div>
                      )}
                      
                      {field.source && (
                         <details className="mt-2 text-xs text-gray-500">
                           <summary className="cursor-pointer hover:text-indigo-600">Why is this asked?</summary>
                           <div className="mt-1 p-2 bg-gray-50 rounded border border-gray-100">
                             <p><strong>Extracted from:</strong> Page {field.source.page}</p>
                             <p><strong>Original field:</strong> {field.source.original_label}</p>
                             {field.source.excerpt && <p className="mt-1 italic">"{field.source.excerpt}"</p>}
                           </div>
                         </details>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            // Supporting Documents Section
            <div className="max-w-2xl">
              <div className="mb-8">
                <h3 className="text-2xl font-bold text-gray-900">Supporting Documents</h3>
                <p className="text-gray-500 mt-1">Upload required documents to verify your application.</p>
              </div>
              
              <div className="space-y-4">
                {formDocument.required_documents.map(doc => {
                  const isUploaded = uploadedDocuments.includes(doc.id);
                  return (
                    <div key={doc.id} className={`p-4 rounded-lg border ${isUploaded ? 'border-green-300 bg-green-50' : 'border-gray-300 bg-white'}`}>
                      <div className="flex justify-between items-start">
                        <div>
                          <h4 className="font-semibold text-gray-900">{doc.name} {doc.required && <span className="text-red-500">*</span>}</h4>
                          <p className="text-sm text-gray-600 mt-1">{doc.description}</p>
                        </div>
                        <div className="ml-4 flex-shrink-0">
                          {isUploaded ? (
                             <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                               Uploaded
                             </span>
                          ) : (
                             <label className="cursor-pointer bg-white border border-gray-300 rounded-md shadow-sm py-1.5 px-3 text-sm leading-4 font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                               <span>Upload</span>
                               <input type="file" className="hidden" accept=".pdf,.png,.jpg,.jpeg" onChange={(e) => handleDocUpload(e, doc.id)} />
                             </label>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Check Results Panel */}
          {checkResult && (
            <div className="mt-8 border-t border-gray-200 pt-8">
               <h3 className="text-xl font-bold text-gray-900 mb-4">Application Check Results</h3>
               <div className={`p-4 rounded-lg border ${checkResult.overall_status === 'clean' ? 'bg-green-50 border-green-200' : checkResult.overall_status === 'warning' ? 'bg-yellow-50 border-yellow-200' : 'bg-red-50 border-red-200'}`}>
                 <h4 className="font-bold text-lg mb-2 capitalize">{checkResult.overall_status}</h4>
                 <div className="space-y-2">
                   {checkResult.categories.map((cat: any, i: number) => (
                     <div key={i} className="flex flex-col text-sm">
                       <span className="font-semibold">{cat.name}: <span className={cat.status === 'passed' ? 'text-green-600' : cat.status === 'warning' ? 'text-yellow-600' : 'text-red-600'}>{cat.status}</span></span>
                       <span className="text-gray-700">{cat.detail}</span>
                     </div>
                   ))}
                 </div>
               </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

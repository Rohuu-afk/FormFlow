import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { analyzeDemo, analyzeDocument } from '../services/api';
import { useFormStore } from '../store/useFormStore';

export default function Landing() {
  const navigate = useNavigate();
  const setFormDocument = useFormStore((s) => s.setFormDocument);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDemo = async () => {
    try {
      setLoading(true);
      setError(null);
      console.log("Calling analyzeDemo...");
      const res = await analyzeDemo();
      console.log("analyzeDemo returned:", res);
      
      setFormDocument(res.form_document, 'demo');
      console.log("setFormDocument complete");
      
      // pre-fill demo values
      useFormStore.getState().setValues({
        full_name: "Priya Sharma",
        date_of_birth: "2003-07-15",
        gender: "Female",
        category: "General",
        aadhaar_number: "9876 5432 1012",
        email: "priya.sharma@example.com",
        phone: "9876543210",
        institution_name: "Government Engineering College, Pune",
        course_name: "B.Tech Computer Science and Engineering",
        year_of_study: "2nd Year",
        percentage_marks: "88.5",
        board_university: "Savitribai Phule Pune University",
        annual_family_income: "240000",
        income_source: "Salaried Employment",
        bank_account_number: "50200012345678",
        ifsc_code: "HDFC0001234",
        address_line1: "12, Shivaji Nagar, Near Railway Station",
        city: "Pune",
        state: "Maharashtra",
        pincode: "411005",
        declaration_accept: true,
        place_of_signing: "Pune",
        date_of_signing: "2024-09-19",
      });
      console.log("setValues complete, navigating...");
      
      navigate('/application');
    } catch (err: any) {
      console.error("handleDemo error:", err);
      setError(err?.response?.data?.detail || err?.message || 'Failed to start demo');
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.[0]) return;
    try {
      setLoading(true);
      setError(null);
      console.log("Calling analyzeDocument...");
      const res = await analyzeDocument(e.target.files[0]);
      console.log("analyzeDocument returned:", res);
      
      setFormDocument(res.form_document, res.mode as 'real' | 'demo');
      console.log("Navigating to application...");
      navigate('/application');
    } catch (err: any) {
      console.error("handleUpload error:", err);
      setError(err?.response?.data?.detail || err?.message || 'Upload failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-8 bg-white shadow-xl rounded-xl">
        <div className="text-center">
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">FormFlow</h2>
          <p className="mt-2 text-sm text-gray-600">Turn complicated forms into guided applications.</p>
        </div>

        {error && (
          <div className="bg-red-50 text-red-700 p-3 rounded-md text-sm">
            {error}
          </div>
        )}

        <div className="space-y-4">
          <button
            onClick={handleDemo}
            disabled={loading}
            className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
          >
            {loading ? 'Processing...' : 'Try Demo'}
          </button>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-gray-500">Or</span>
            </div>
          </div>

          <div>
            <label className="w-full flex justify-center py-3 px-4 border-2 border-dashed border-gray-300 rounded-md cursor-pointer hover:border-indigo-500 hover:bg-gray-50 transition-colors">
              <span className="text-sm font-medium text-gray-700">Upload Document (PDF, Image)</span>
              <input type="file" className="hidden" accept=".pdf,.png,.jpg,.jpeg,.webp" onChange={handleUpload} disabled={loading} />
            </label>
          </div>
        </div>
      </div>
    </div>
  );
}

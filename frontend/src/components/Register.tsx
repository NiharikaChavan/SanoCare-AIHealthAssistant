import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

interface RegisterFormData {
    // Basic Information
    username: string;
    email: string;
    password: string;
    date_of_birth: string;
    gender: string;
    
    // Essential Cultural and Demographic Information
    ethnicity: string;
    region: string;
    city: string;
    occupation: string;
    language_preference: string;
    
    // Health Information
    blood_type: string;
    allergies: string;
    chronic_conditions: string;
    medications: string;
    family_history: string;
    traditional_medicine_preferences: {
        modern: boolean;
        ayurveda?: boolean;
        tcm?: boolean;
        kampo?: boolean;
        unani?: boolean;
        homeopathy?: boolean;
        other?: string;
    };
    
    // Medical History
    medical_history: string;
    vaccination_history: string;
    last_checkup: string;
}

const Register: React.FC = () => {
    const navigate = useNavigate();
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const { setUser } = useAuth();
    const [formData, setFormData] = useState<RegisterFormData>({
        // Basic Information
        username: '',
        email: '',
        password: '',
        date_of_birth: '',
        gender: '',
        
        // Essential Cultural and Demographic Information
        ethnicity: '',
        region: '',
        city: '',
        occupation: '',
        language_preference: '',
        
        // Health Information
        blood_type: '',
        allergies: '',
        chronic_conditions: '',
        medications: '',
        family_history: '',
        traditional_medicine_preferences: {
            modern: true,
            ayurveda: false,
            tcm: false,
            kampo: false,
            unani: false,
            homeopathy: false,
            other: ''
        },
        
        // Medical History
        medical_history: '',
        vaccination_history: '',
        last_checkup: ''
    });

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        const { name, value, type } = e.target;
        
        if (name.startsWith('traditional_medicine_')) {
            const prefName = name.split('_')[2];
            setFormData(prev => ({
                ...prev,
                traditional_medicine_preferences: {
                    ...prev.traditional_medicine_preferences,
                    [prefName]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value
                }
            }));
        } else {
            setFormData(prev => ({
                ...prev,
                [name]: value
            }));
        }
    };

    const getRegionSpecificMedicineOptions = () => {
        switch (formData.region) {
            case 'asia':
                return (
                    <>
                        <div className="mb-2">
                            <label className="flex items-center">
                                <input
                                    type="checkbox"
                                    name="traditional_medicine_ayurveda"
                                    checked={formData.traditional_medicine_preferences.ayurveda}
                                    onChange={handleChange}
                                    className="mr-2"
                                />
                                Ayurveda
                            </label>
                        </div>
                        <div className="mb-2">
                            <label className="flex items-center">
                                <input
                                    type="checkbox"
                                    name="traditional_medicine_tcm"
                                    checked={formData.traditional_medicine_preferences.tcm}
                                    onChange={handleChange}
                                    className="mr-2"
                                />
                                Traditional Chinese Medicine (TCM)
                            </label>
                        </div>
                        <div className="mb-2">
                            <label className="flex items-center">
                                <input
                                    type="checkbox"
                                    name="traditional_medicine_kampo"
                                    checked={formData.traditional_medicine_preferences.kampo}
                                    onChange={handleChange}
                                    className="mr-2"
                                />
                                Kampo (Japanese Traditional Medicine)
                            </label>
                        </div>
                    </>
                );
            case 'middle_east':
                return (
                    <>
                        <div className="mb-2">
                            <label className="flex items-center">
                                <input
                                    type="checkbox"
                                    name="traditional_medicine_unani"
                                    checked={formData.traditional_medicine_preferences.unani}
                                    onChange={handleChange}
                                    className="mr-2"
                                />
                                Unani Medicine
                            </label>
                        </div>
                    </>
                );
            default:
                return (
                    <>
                        <div className="mb-2">
                            <label className="flex items-center">
                                <input
                                    type="checkbox"
                                    name="traditional_medicine_homeopathy"
                                    checked={formData.traditional_medicine_preferences.homeopathy}
                                    onChange={handleChange}
                                    className="mr-2"
                                />
                                Homeopathy
                            </label>
                        </div>
                    </>
                );
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        try {
            console.log('Sending registration data:', formData);
            console.log('API URL:', API_URL);
            
            const response = await fetch(`${API_URL}/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                },
                body: JSON.stringify(formData),
                credentials: 'include'
            });

            console.log('Response status:', response.status);
            console.log('Response headers:', Object.fromEntries(response.headers.entries()));

            let data;
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                data = await response.json();
                console.log('Response data:', data);
            } else {
                const text = await response.text();
                console.error('Non-JSON response:', text);
                throw new Error('Server returned invalid response format');
            }

            if (response.ok) {
                console.log('Registration successful:', data);
                setUser(data.user);
                navigate('/chat');
            } else {
                console.error('Registration failed:', data);
                setError(data.message || 'Registration failed');
            }
        } catch (err) {
            console.error('Registration error:', err);
            setError('An error occurred during registration. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen relative overflow-hidden bg-gradient-to-br from-slate-50 via-white to-blue-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
            {/* Dynamic Background */}
            <div className="absolute inset-0 z-0">
                {/* Base Gradient */}
                <div className="absolute inset-0 bg-gradient-to-br from-slate-100/30 via-white/50 to-blue-100/30 dark:from-slate-800/20 dark:via-slate-800/50 dark:to-slate-800/20" />
                
                {/* Animated Grid Pattern */}
                <div className="absolute inset-0 opacity-20 dark:opacity-30">
                    <div className="absolute inset-0 bg-[linear-gradient(to_right,#10B98112_1px,transparent_1px),linear-gradient(to_bottom,#10B98112_1px,transparent_1px)] bg-[size:24px_24px] animate-grid" />
                </div>
                
                {/* Floating Elements */}
                <div className="absolute inset-0 overflow-hidden">
                    {/* Animated Circles */}
                    <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-slate-200/30 dark:bg-slate-800/30 rounded-full blur-3xl animate-pulse" />
                    <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-200/30 dark:bg-blue-900/30 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
                </div>
            </div>

            {/* Content */}
            <div className="relative z-10 min-h-screen flex items-center justify-center py-12 px-4">
                <div className="w-full max-w-3xl">
                    <div className="text-center mb-8">
                        <h2 className="text-3xl font-bold bg-gradient-to-r from-slate-600 to-blue-600 dark:from-slate-400 dark:to-blue-400 bg-clip-text text-transparent">
                            Create Your Account
                        </h2>
                        <p className="mt-2 text-slate-600 dark:text-slate-400">
                            Join SanoCare AI for personalized health guidance
                        </p>
                    </div>

                    <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm p-8 rounded-2xl shadow-lg border border-slate-200/50 dark:border-slate-700/50">
                        {error && (
                            <div className="bg-red-100 dark:bg-red-900/30 border border-red-400 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg relative mb-6">
                                {error}
                            </div>
                        )}

                        <form onSubmit={handleSubmit} className="space-y-6">
                            {/* Basic Information Section */}
                            <div className="bg-slate-50/50 dark:bg-slate-700/50 p-6 rounded-xl">
                                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Basic Information</h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-slate-700 dark:text-slate-300 text-sm font-medium mb-2">
                                            Username
                                        </label>
                                        <input
                                            type="text"
                                            name="username"
                                            value={formData.username}
                                            onChange={handleChange}
                                            required
                                            className="w-full px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-600 dark:focus:ring-slate-400 focus:border-transparent"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-slate-700 dark:text-slate-300 text-sm font-medium mb-2">
                                            Email
                                        </label>
                                        <input
                                            type="email"
                                            name="email"
                                            value={formData.email}
                                            onChange={handleChange}
                                            required
                                            className="w-full px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-600 dark:focus:ring-slate-400 focus:border-transparent"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-slate-700 dark:text-slate-300 text-sm font-medium mb-2">
                                            Password
                                        </label>
                                        <input
                                            type="password"
                                            name="password"
                                            value={formData.password}
                                            onChange={handleChange}
                                            required
                                            className="w-full px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-600 dark:focus:ring-slate-400 focus:border-transparent"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-slate-700 dark:text-slate-300 text-sm font-medium mb-2">
                                            Date of Birth
                                        </label>
                                        <input
                                            type="date"
                                            name="date_of_birth"
                                            value={formData.date_of_birth}
                                            onChange={handleChange}
                                            required
                                            className="w-full px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-600 dark:focus:ring-slate-400 focus:border-transparent"
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* Cultural and Demographic Section */}
                            <div className="bg-slate-50/50 dark:bg-slate-700/50 p-6 rounded-xl">
                                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Cultural & Demographic Information</h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-slate-700 dark:text-slate-300 text-sm font-medium mb-2">
                                            Ethnicity
                                        </label>
                                        <input
                                            type="text"
                                            name="ethnicity"
                                            value={formData.ethnicity}
                                            onChange={handleChange}
                                            className="w-full px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-600 dark:focus:ring-slate-400 focus:border-transparent"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-slate-700 dark:text-slate-300 text-sm font-medium mb-2">
                                            Region
                                        </label>
                                        <input
                                            type="text"
                                            name="region"
                                            value={formData.region}
                                            onChange={handleChange}
                                            className="w-full px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-600 dark:focus:ring-slate-400 focus:border-transparent"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-slate-700 dark:text-slate-300 text-sm font-medium mb-2">
                                            City
                                        </label>
                                        <input
                                            type="text"
                                            name="city"
                                            value={formData.city}
                                            onChange={handleChange}
                                            className="w-full px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-600 dark:focus:ring-slate-400 focus:border-transparent"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-slate-700 dark:text-slate-300 text-sm font-medium mb-2">
                                            Occupation
                                        </label>
                                        <input
                                            type="text"
                                            name="occupation"
                                            value={formData.occupation}
                                            onChange={handleChange}
                                            className="w-full px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-600 dark:focus:ring-slate-400 focus:border-transparent"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-slate-700 dark:text-slate-300 text-sm font-medium mb-2">
                                            Preferred Language
                                        </label>
                                        <select
                                            name="language_preference"
                                            value={formData.language_preference}
                                            onChange={handleChange}
                                            className="w-full px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-600 dark:focus:ring-slate-400 focus:border-transparent"
                                        >
                                            <option value="">Select preferred language</option>
                                            <option value="en">English</option>
                                            <option value="es">Spanish</option>
                                            <option value="fr">French</option>
                                            <option value="de">German</option>
                                            <option value="hi">Hindi</option>
                                            <option value="other">Other</option>
                                        </select>
                                    </div>
                                </div>
                            </div>

                            {/* Health Information Section */}
                            <div className="bg-slate-50/50 dark:bg-slate-700/50 p-6 rounded-xl">
                                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Health Information</h3>
                                <div className="grid grid-cols-1 gap-4">
                                    <div>
                                        <label className="block text-slate-700 dark:text-slate-300 text-sm font-medium mb-2">
                                            Blood Type
                                        </label>
                                        <select
                                            name="blood_type"
                                            value={formData.blood_type}
                                            onChange={handleChange}
                                            className="w-full px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-600 dark:focus:ring-slate-400 focus:border-transparent"
                                        >
                                            <option value="">Select blood type</option>
                                            <option value="A+">A+</option>
                                            <option value="A-">A-</option>
                                            <option value="B+">B+</option>
                                            <option value="B-">B-</option>
                                            <option value="AB+">AB+</option>
                                            <option value="AB-">AB-</option>
                                            <option value="O+">O+</option>
                                            <option value="O-">O-</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-slate-700 dark:text-slate-300 text-sm font-medium mb-2">
                                            Allergies
                                        </label>
                                        <textarea
                                            name="allergies"
                                            value={formData.allergies}
                                            onChange={handleChange}
                                            rows={2}
                                            className="w-full px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-600 dark:focus:ring-slate-400 focus:border-transparent"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-slate-700 dark:text-slate-300 text-sm font-medium mb-2">
                                            Chronic Conditions
                                        </label>
                                        <textarea
                                            name="chronic_conditions"
                                            value={formData.chronic_conditions}
                                            onChange={handleChange}
                                            rows={2}
                                            className="w-full px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-600 dark:focus:ring-slate-400 focus:border-transparent"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-slate-700 dark:text-slate-300 text-sm font-medium mb-2">
                                            Current Medications
                                        </label>
                                        <textarea
                                            name="medications"
                                            value={formData.medications}
                                            onChange={handleChange}
                                            rows={2}
                                            className="w-full px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-600 dark:focus:ring-slate-400 focus:border-transparent"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-slate-700 dark:text-slate-300 text-sm font-medium mb-2">
                                            Family History
                                        </label>
                                        <textarea
                                            name="family_history"
                                            value={formData.family_history}
                                            onChange={handleChange}
                                            rows={2}
                                            className="w-full px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-600 dark:focus:ring-slate-400 focus:border-transparent"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-slate-700 dark:text-slate-300 text-sm font-medium mb-2">
                                            Traditional Medicine Preferences
                                        </label>
                                        <div className="space-y-4">
                                            <div className="mb-4">
                                                <label className="flex items-center">
                                                    <input
                                                        type="checkbox"
                                                        name="traditional_medicine_modern"
                                                        checked={formData.traditional_medicine_preferences.modern}
                                                        onChange={handleChange}
                                                        className="mr-2"
                                                    />
                                                    Modern Medicine
                                                </label>
                                            </div>
                                            
                                            {getRegionSpecificMedicineOptions()}
                                            
                                            <div className="mb-2">
                                                <label className="block text-slate-700 dark:text-slate-300 text-sm font-medium">
                                                    Other Traditional Medicine (if any)
                                                </label>
                                                <input
                                                    type="text"
                                                    name="traditional_medicine_other"
                                                    value={formData.traditional_medicine_preferences.other}
                                                    onChange={handleChange}
                                                    className="w-full px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-600 dark:focus:ring-slate-400 focus:border-transparent"
                                                    placeholder="Specify other traditional medicine practices"
                                                />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="flex items-center justify-between pt-6">
                                <button
                                    type="submit"
                                    disabled={isLoading}
                                    className={`bg-gradient-to-r from-slate-600 to-blue-600 hover:from-slate-700 hover:to-blue-700 text-white font-medium py-2 px-6 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                                        isLoading ? 'opacity-50 cursor-not-allowed' : ''
                                    }`}
                                >
                                    {isLoading ? 'Creating Account...' : 'Create Account'}
                                </button>
                                <Link
                                    to="/login"
                                    className="text-sm font-medium text-slate-600 hover:text-blue-600 dark:text-slate-400 dark:hover:text-blue-400"
                                >
                                    Already have an account? Sign in
                                </Link>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Register; 
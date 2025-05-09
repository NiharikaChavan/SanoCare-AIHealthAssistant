import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Heart } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

const Login: React.FC = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const navigate = useNavigate();
    const { setUser } = useAuth();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);
        
        try {
            const response = await fetch(`${API_URL}/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password }),
                credentials: 'include'
            });

            let data;
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                data = await response.json();
            } else {
                const text = await response.text();
                console.error('Non-JSON response:', text);
                throw new Error('Server returned invalid response format');
            }

            if (response.ok) {
                setUser(data.user);
                navigate('/chat');
            } else {
                setError(data.message || 'Login failed');
            }
        } catch (err) {
            console.error('Login error:', err);
            setError('An error occurred during login. Please try again.');
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
            <div className="relative z-10 min-h-screen flex items-center justify-center px-4">
                <div className="w-full max-w-md">
                    <div className="text-center mb-8">
                        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-br from-slate-100 to-blue-100 dark:from-slate-800 dark:to-blue-900 flex items-center justify-center">
                            <Heart className="w-8 h-8 text-slate-600 dark:text-slate-400" />
                        </div>
                        <h2 className="text-3xl font-bold bg-gradient-to-r from-slate-600 to-blue-600 dark:from-slate-400 dark:to-blue-400 bg-clip-text text-transparent">
                            Welcome Back
                        </h2>
                        <p className="mt-2 text-slate-600 dark:text-slate-400">
                            Sign in to continue to SanoCare AI
                        </p>
                    </div>

                    <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm p-8 rounded-2xl shadow-lg border border-slate-200/50 dark:border-slate-700/50">
                        {error && (
                            <div className="bg-red-100 dark:bg-red-900/30 border border-red-400 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg relative mb-4">
                                {error}
                            </div>
                        )}
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="block text-slate-700 dark:text-slate-300 text-sm font-medium mb-2" htmlFor="email">
                                    Email
                                </label>
                                <input
                                    className="w-full px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-600 dark:focus:ring-slate-400 focus:border-transparent"
                                    id="email"
                                    type="email"
                                    placeholder="Enter your email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                    disabled={isLoading}
                                />
                            </div>
                            <div>
                                <label className="block text-slate-700 dark:text-slate-300 text-sm font-medium mb-2" htmlFor="password">
                                    Password
                                </label>
                                <input
                                    className="w-full px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-600 dark:focus:ring-slate-400 focus:border-transparent"
                                    id="password"
                                    type="password"
                                    placeholder="Enter your password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                    disabled={isLoading}
                                />
                            </div>
                            <div className="flex items-center justify-between pt-2">
                                <button
                                    className={`bg-gradient-to-r from-slate-600 to-blue-600 hover:from-slate-700 hover:to-blue-700 text-white font-medium py-2 px-6 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                                        isLoading ? 'opacity-50 cursor-not-allowed' : ''
                                    }`}
                                    type="submit"
                                    disabled={isLoading}
                                >
                                    {isLoading ? 'Signing in...' : 'Sign In'}
                                </button>
                                <Link
                                    to="/register"
                                    className="text-sm font-medium text-slate-600 hover:text-blue-600 dark:text-slate-400 dark:hover:text-blue-400"
                                >
                                    Create an account
                                </Link>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Login; 
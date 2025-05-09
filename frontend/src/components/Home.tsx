import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Heart, MessageSquare, Stethoscope, Brain, Shield, Lungs, Bone, Muscle } from 'lucide-react';

const Home: React.FC = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: <Stethoscope className="w-8 h-8 text-health" />,
      title: "AI-Powered Diagnosis",
      description: "Get instant, accurate health assessments based on your symptoms and medical history."
    },
    {
      icon: <Brain className="w-8 h-8 text-health" />,
      title: "Smart Health Assistant",
      description: "Our AI understands your health concerns and provides personalized medical guidance."
    },
    {
      icon: <Shield className="w-8 h-8 text-health" />,
      title: "Privacy & Security",
      description: "Your health data is protected with advanced security measures and strict privacy policies."
    }
  ];

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
          
          {/* Abstract Medical Elements */}
          <div className="absolute top-1/3 right-1/3 w-32 h-32 border-4 border-slate-200/30 dark:border-slate-800/30 rounded-full animate-spin-slow" />
          <div className="absolute bottom-1/3 left-1/3 w-24 h-24 border-4 border-blue-200/30 dark:border-blue-900/30 rounded-full animate-spin-slow" style={{ animationDelay: '2s' }} />
          
          {/* DNA-like Helix Pattern */}
          <div className="absolute inset-0 opacity-10">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,#3B82F6_0%,transparent_50%)] animate-helix" />
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,#64748B_0%,transparent_50%)] animate-helix" style={{ animationDelay: '1s' }} />
          </div>
        </div>
        
        {/* Overlay */}
        <div className="absolute inset-0 bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm" />
      </div>

      {/* Content */}
      <div className="relative z-10">
        {/* Hero Section */}
        <div className="container mx-auto px-4 py-16">
          <div className="text-center max-w-3xl mx-auto">
            <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-slate-600 to-blue-600 dark:from-slate-400 dark:to-blue-400 bg-clip-text text-transparent mb-6">
              Your Personal AI Health Assistant
            </h1>
            <p className="text-xl text-slate-600 dark:text-slate-300 mb-8">
              Get instant, accurate health guidance powered by advanced AI technology. 
              Your health companion for better well-being.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button 
                onClick={() => navigate('/chat')}
                className="bg-gradient-to-r from-slate-600 to-blue-600 hover:from-slate-700 hover:to-blue-700 text-white shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105"
              >
                <MessageSquare className="w-4 h-4 mr-2" />
                Start Chat
              </Button>
              <Button 
                onClick={() => navigate('/register')}
                variant="outline"
                className="border-slate-600 text-slate-600 hover:bg-slate-50 dark:border-slate-400 dark:text-slate-400 dark:hover:bg-slate-800/30 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105"
              >
                Create Account
              </Button>
            </div>
          </div>
        </div>

        {/* Features Section */}
        <div className="container mx-auto px-4 py-16">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div 
                key={index}
                className="bg-white/90 dark:bg-slate-800/90 backdrop-blur-sm p-6 rounded-lg shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 border border-slate-100 dark:border-slate-700"
              >
                <div className="w-12 h-12 bg-gradient-to-br from-slate-100 to-blue-100 dark:from-slate-800/30 dark:to-blue-800/30 rounded-full flex items-center justify-center mb-4">
                  {feature.icon}
                </div>
                <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
                  {feature.title}
                </h3>
                <p className="text-slate-600 dark:text-slate-300">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* CTA Section */}
        <div className="bg-gradient-to-r from-slate-50 to-blue-50 dark:from-slate-800/20 dark:to-blue-800/20 py-16 backdrop-blur-sm">
          <div className="container mx-auto px-4 text-center">
            <h2 className="text-3xl font-bold bg-gradient-to-r from-slate-600 to-blue-600 dark:from-slate-400 dark:to-blue-400 bg-clip-text text-transparent mb-4">
              Ready to Take Control of Your Health?
            </h2>
            <p className="text-xl text-slate-600 dark:text-slate-300 mb-8 max-w-2xl mx-auto">
              Join thousands of users who trust our AI Health Assistant for reliable medical guidance and support.
            </p>
            <Button 
              onClick={() => navigate('/register')}
              className="bg-gradient-to-r from-slate-600 to-blue-600 hover:from-slate-700 hover:to-blue-700 text-white shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105"
            >
              Get Started Now
            </Button>
          </div>
        </div>

        <div className="max-w-4xl mx-auto px-4 py-12">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="space-y-6">
              <h2 className="text-3xl font-bold text-slate-900 dark:text-white">
                Interactive Health Education
              </h2>
              <p className="text-slate-600 dark:text-slate-300">
                Explore the human body in 3D and learn about different body systems.
              </p>
              <button
                onClick={() => navigate('/vr-health')}
                className="bg-gradient-to-r from-slate-600 to-blue-600 hover:from-slate-700 hover:to-blue-700 text-white font-medium py-3 px-6 rounded-lg transition-colors"
              >
                Start VR Experience
              </button>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="p-6 bg-white/50 dark:bg-slate-800/50 rounded-xl backdrop-blur-sm">
                <Heart className="w-12 h-12 text-red-500 mb-4" />
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Circulatory System</h3>
              </div>
              <div className="p-6 bg-white/50 dark:bg-slate-800/50 rounded-xl backdrop-blur-sm">
                <Brain className="w-12 h-12 text-blue-500 mb-4" />
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Nervous System</h3>
              </div>
              <div className="p-6 bg-white/50 dark:bg-slate-800/50 rounded-xl backdrop-blur-sm">
                <Lungs className="w-12 h-12 text-green-500 mb-4" />
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Respiratory System</h3>
              </div>
              <div className="p-6 bg-white/50 dark:bg-slate-800/50 rounded-xl backdrop-blur-sm">
                <Bone className="w-12 h-12 text-yellow-500 mb-4" />
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Skeletal System</h3>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home; 
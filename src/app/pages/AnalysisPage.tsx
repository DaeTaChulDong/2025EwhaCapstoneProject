import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Progress } from '../components/ui/progress';
import { PlayCircle, CheckCircle2 } from 'lucide-react';

const ANALYSIS_STEPS = [
  { id: 1, text: "선택한 카테고리의 최신 '성공 공식' 로딩 중...", duration: 1500, subtitle: 'Update: 오늘 09:00' },
  { id: 2, text: '영상 프레임 및 오디오 분석 중...', duration: 2000 },
  { id: 3, text: '맥락 분석 및 키워드 추출 중...', duration: 2000 },
  { id: 4, text: '시장 데이터와 비교 분석 중...', duration: 1500 },
  { id: 5, text: '맞춤형 컨설팅 리포트 생성 완료!', duration: 1000 },
];

export default function AnalysisPage() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (currentStep < ANALYSIS_STEPS.length) {
      const step = ANALYSIS_STEPS[currentStep];
      const duration = step.duration;
      
      // Progress animation
      const progressInterval = setInterval(() => {
        setProgress((prev) => {
          const increment = 100 / (duration / 50);
          return Math.min(prev + increment, ((currentStep + 1) / ANALYSIS_STEPS.length) * 100);
        });
      }, 50);

      // Move to next step
      const stepTimeout = setTimeout(() => {
        if (currentStep < ANALYSIS_STEPS.length - 1) {
          setCurrentStep(currentStep + 1);
        } else {
          // Analysis complete, navigate to results
          setTimeout(() => {
            navigate('/result');
          }, 1000);
        }
      }, duration);

      return () => {
        clearInterval(progressInterval);
        clearTimeout(stepTimeout);
      };
    }
  }, [currentStep, navigate]);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white px-8 py-6 flex items-center border-b border-gray-100">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 bg-[#F04645] rounded-lg flex items-center justify-center">
            <PlayCircle className="w-6 h-6 text-white" />
          </div>
          <span className="text-2xl font-bold text-gray-900">Hookly</span>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center px-8">
        <div className="max-w-2xl w-full">
          <div className="text-center mb-12">
            <h1 className="text-3xl mb-3">AI가 영상을 정밀 분석 중입니다</h1>
            <p className="text-gray-600">약 1분 정도 소요됩니다. 잠시만 기다려주세요.</p>
          </div>

          {/* Progress Bar */}
          <div className="mb-12">
            <Progress value={progress} className="h-3 mb-3" />
            <div className="text-right text-sm text-gray-600">
              {Math.round(progress)}%
            </div>
          </div>

          {/* Analysis Steps */}
          <div className="space-y-4">
            {ANALYSIS_STEPS.map((step, index) => (
              <div
                key={step.id}
                className={`flex items-start gap-4 p-4 rounded-lg transition-all ${
                  index <= currentStep
                    ? 'bg-white border border-gray-200'
                    : 'bg-gray-50 border border-transparent'
                }`}
              >
                <div className="flex-shrink-0 mt-1">
                  {index < currentStep ? (
                    <CheckCircle2 className="w-6 h-6 text-green-500" />
                  ) : index === currentStep ? (
                    <div className="w-6 h-6 border-4 border-[#F04645] border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <div className="w-6 h-6 border-2 border-gray-300 rounded-full" />
                  )}
                </div>
                <div className="flex-1">
                  <p
                    className={`${
                      index <= currentStep
                        ? 'text-gray-900 font-medium'
                        : 'text-gray-400'
                    }`}
                  >
                    {step.text}
                  </p>
                  {step.subtitle && index === currentStep && (
                    <p className="text-sm text-[#F04645] mt-1">{step.subtitle}</p>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Loading Animation */}
          <div className="mt-12 text-center">
            <div className="inline-flex items-center gap-2 text-gray-500">
              <div className="w-2 h-2 bg-[#F04645] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <div className="w-2 h-2 bg-[#F04645] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <div className="w-2 h-2 bg-[#F04645] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

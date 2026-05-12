'use client'

import { useState } from 'react'

const LANGUAGES = [
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'ar', name: 'العربية', flag: '🇸🇦' },
  { code: 'ms', name: 'Bahasa Melayu', flag: '🇲🇾' },
  { code: 'id', name: 'Bahasa Indonesia', flag: '🇮🇩' },
]

const PLATFORMS = [
  { id: 'instagram', name: 'Instagram', color: 'from-purple-500 to-pink-500' },
  { id: 'facebook', name: 'Facebook', color: 'from-blue-500 to-blue-700' },
  { id: 'twitter', name: 'Twitter', color: 'from-sky-400 to-sky-600' },
  { id: 'tiktok', name: 'TikTok', color: 'from-pink-400 to-rose-500' },
]

export default function Home() {
  const [product, setProduct] = useState('')
  const [brand, setBrand] = useState('')
  const [platforms, setPlatforms] = useState(['instagram'])
  const [language, setLanguage] = useState('en')
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(false)
  const [generatedContent, setGeneratedContent] = useState(null)

  const generateContent = async () => {
    if (!product) {
      alert('Please enter a product name')
      return
    }

    setLoading(true)
    setGeneratedContent(null)

    // Simulated AI generation (in production, use OpenAI API)
    setTimeout(() => {
      const mockContent = generateMockContent(product, brand, platforms, language)
      setGeneratedContent(mockContent)
      setLoading(false)
    }, 2000)
  }

  const generateMockContent = (product, brand, platforms, lang) => {
    const translations = {
      en: {
        intro: `✨ Introducing ${product}${brand ? ` by ${brand}` : ''}!`,
        hashtags: ['#newproduct', '#innovation', '#mustbuy', '#trending'],
      },
      ar: {
        intro: `✨ نقدم لكم ${product}${brand ? ` من ${brand}` : ''}!`,
        hashtags: ['#منتج_جديد', '#ابتكار', '#لا_تفوّت', '#رائج'],
      },
      ms: {
        intro: `✨ Perkenalkan ${product}${brand ? ` oleh ${brand}` : ''}!`,
        hashtags: ['#produkbaru', '#inovasi', '#harusbeli', '#trending'],
      },
      id: {
        intro: `✨ Perkenalkan ${product}${brand ? ` oleh ${brand}` : ''}!`,
        hashtags: ['#produkbaru', '#inovasi', '#wajibbeli', '#trending'],
      },
    }

    const t = translations[lang] || translations.en
    const platformContent = {}

    platforms.forEach(p => {
      const templates = {
        instagram: {
          headline: t.intro,
          body: `Don't miss this amazing product! Tap the link in bio for more details.`,
          hashtags: t.hashtags.join(' '),
        },
        facebook: {
          headline: t.intro,
          body: `We're thrilled to share ${product} with you! This is going to change everything. Share with friends who might love it too!`,
          hashtags: t.hashtags.join(' '),
        },
        twitter: {
          headline: t.intro,
          body: `You NEED to check this out! 🔥`,
          hashtags: t.hashtags.slice(0, 2).join(' '),
        },
        tiktok: {
          headline: `POV: You just discovered ${product}`,
          body: `Wait for it... 🤯 #fyp #viral #${product.replace(/\s/g, '')}`,
          hashtags: t.hashtags.slice(0, 3).join(' '),
        },
      }
      platformContent[p] = templates[p] || templates.instagram
    })

    return platformContent
  }

  const togglePlatform = (id) => {
    setPlatforms(prev =>
      prev.includes(id) ? prev.filter(p => p !== id) : [...prev, id]
    )
  }

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
    alert('Copied to clipboard!')
  }

  return (
    <main className="min-h-screen">
      {/* Hero Section */}
      <section className="relative py-20 px-4 text-center">
        <div className="max-w-4xl mx-auto">
          <div className="mb-6 inline-block">
            <span className="px-4 py-2 rounded-full text-sm font-medium bg-primary/20 text-primary border border-primary/30">
              🚀 AI-Powered Content Generation
            </span>
          </div>
          <h1 className="text-5xl md:text-7xl font-bold mb-6">
            <span className="gradient-text">ContentAI</span>
          </h1>
          <p className="text-xl text-gray-400 mb-8 max-w-2xl mx-auto">
            Generate engaging social media content in multiple languages instantly.
            Perfect for businesses in Southeast Asia and Middle East markets.
          </p>
          <div className="flex flex-wrap justify-center gap-4 text-sm text-gray-500">
            <span className="px-3 py-1 rounded-full bg-white/5 border border-white/10">
              🇸🇦 Arabic Support
            </span>
            <span className="px-3 py-1 rounded-full bg-white/5 border border-white/10">
              🇲🇾 Malay Support
            </span>
            <span className="px-3 py-1 rounded-full bg-white/5 border border-white/10">
              🇮🇩 Indonesian Support
            </span>
            <span className="px-3 py-1 rounded-full bg-white/5 border border-white/10">
              🇺🇸 English Support
            </span>
          </div>
        </div>
      </section>

      {/* Generator Section */}
      <section className="py-12 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="glass rounded-2xl p-8">
            <h2 className="text-2xl font-bold mb-6 text-center">Create Your Content</h2>

            {/* Input Fields */}
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Product Name *
                </label>
                <input
                  type="text"
                  value={product}
                  onChange={(e) => setProduct(e.target.value)}
                  placeholder="e.g., Organic Coffee Beans"
                  className="w-full px-4 py-3 rounded-lg bg-white/5 border border-white/10 focus:border-primary focus:outline-none text-white placeholder-gray-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Brand Name (optional)
                </label>
                <input
                  type="text"
                  value={brand}
                  onChange={(e) => setBrand(e.target.value)}
                  placeholder="e.g., CoffeeCo"
                  className="w-full px-4 py-3 rounded-lg bg-white/5 border border-white/10 focus:border-primary focus:outline-none text-white placeholder-gray-500"
                />
              </div>

              {/* Platform Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-3">
                  Target Platforms
                </label>
                <div className="flex flex-wrap gap-3">
                  {PLATFORMS.map((p) => (
                    <button
                      key={p.id}
                      onClick={() => togglePlatform(p.id)}
                      className={`px-4 py-2 rounded-lg font-medium transition-all ${
                        platforms.includes(p.id)
                          ? `bg-gradient-to-r ${p.color} text-white`
                          : 'bg-white/5 text-gray-400 hover:bg-white/10'
                      }`}
                    >
                      {p.name}
                    </button>
                  ))}
                </div>
              </div>

              {/* Language Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-3">
                  Content Language
                </label>
                <div className="flex flex-wrap gap-3">
                  {LANGUAGES.map((lang) => (
                    <button
                      key={lang.code}
                      onClick={() => setLanguage(lang.code)}
                      className={`px-4 py-2 rounded-lg font-medium transition-all ${
                        language === lang.code
                          ? 'bg-primary text-white'
                          : 'bg-white/5 text-gray-400 hover:bg-white/10'
                      }`}
                    >
                      {lang.flag} {lang.name}
                    </button>
                  ))}
                </div>
              </div>

              {/* Generate Button */}
              <button
                onClick={generateContent}
                disabled={loading}
                className="w-full py-4 rounded-lg font-bold text-lg btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Generating...
                  </span>
                ) : (
                  '✨ Generate Content'
                )}
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Generated Content Section */}
      {generatedContent && (
        <section className="py-12 px-4">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-2xl font-bold mb-6 text-center">Generated Content</h2>
            <div className="grid gap-6">
              {Object.entries(generatedContent).map(([platform, content]) => {
                const platformInfo = PLATFORMS.find(p => p.id === platform)
                return (
                  <div key={platform} className="card rounded-xl p-6">
                    <div className="flex items-center gap-3 mb-4">
                      <div className={`w-10 h-10 rounded-lg bg-gradient-to-r ${platformInfo?.color || 'from-gray-500 to-gray-600'} flex items-center justify-center text-white font-bold`}>
                        {platform[0].toUpperCase()}
                      </div>
                      <h3 className="text-lg font-semibold capitalize">{platform}</h3>
                    </div>
                    <div className="space-y-3">
                      <div>
                        <p className="text-xs text-gray-500 uppercase tracking-wide">Headline</p>
                        <p className="text-white">{content.headline}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500 uppercase tracking-wide">Caption</p>
                        <p className="text-gray-300">{content.body}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500 uppercase tracking-wide">Hashtags</p>
                        <p className="text-primary">{content.hashtags}</p>
                      </div>
                      <button
                        onClick={() => copyToClipboard(`${content.headline}\n\n${content.body}\n\n${content.hashtags}`)}
                        className="mt-4 px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white text-sm font-medium transition-all"
                      >
                        📋 Copy to Clipboard
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </section>
      )}

      {/* Pricing Section */}
      <section className="py-20 px-4" id="pricing">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold mb-4 text-center">
            Simple <span className="gradient-text">Pricing</span>
          </h2>
          <p className="text-gray-400 text-center mb-12">
            Start free, upgrade when you need more
          </p>

          <div className="grid md:grid-cols-3 gap-6">
            {/* Free Tier */}
            <div className="card rounded-2xl p-6">
              <div className="text-center mb-6">
                <h3 className="text-xl font-bold mb-2">Free</h3>
                <p className="text-4xl font-bold">$0</p>
                <p className="text-gray-500">forever</p>
              </div>
              <ul className="space-y-3 mb-6">
                <li className="flex items-center gap-2 text-gray-300">
                  <span className="text-green-400">✓</span> 5 generations/day
                </li>
                <li className="flex items-center gap-2 text-gray-300">
                  <span className="text-green-400">✓</span> English only
                </li>
                <li className="flex items-center gap-2 text-gray-500">
                  <span className="text-red-400">✗</span> No multi-platform
                </li>
              </ul>
              <button className="w-full py-3 rounded-lg bg-white/10 hover:bg-white/20 text-white font-medium transition-all">
                Get Started
              </button>
            </div>

            {/* Pro Tier */}
            <div className="card rounded-2xl p-6 border-primary animate-pulse-glow relative">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full bg-primary text-xs font-bold">
                POPULAR
              </div>
              <div className="text-center mb-6">
                <h3 className="text-xl font-bold mb-2">Pro</h3>
                <p className="text-4xl font-bold">$9.99</p>
                <p className="text-gray-500">per month</p>
              </div>
              <ul className="space-y-3 mb-6">
                <li className="flex items-center gap-2 text-gray-300">
                  <span className="text-green-400">✓</span> Unlimited generations
                </li>
                <li className="flex items-center gap-2 text-gray-300">
                  <span className="text-green-400">✓</span> All 4 languages
                </li>
                <li className="flex items-center gap-2 text-gray-300">
                  <span className="text-green-400">✓</span> All platforms
                </li>
                <li className="flex items-center gap-2 text-gray-300">
                  <span className="text-green-400">✓</span> Priority support
                </li>
              </ul>
              <button className="w-full py-3 rounded-lg btn-primary text-white font-bold">
                Start Free Trial
              </button>
            </div>

            {/* Enterprise Tier */}
            <div className="card rounded-2xl p-6">
              <div className="text-center mb-6">
                <h3 className="text-xl font-bold mb-2">Enterprise</h3>
                <p className="text-4xl font-bold">$29</p>
                <p className="text-gray-500">per month</p>
              </div>
              <ul className="space-y-3 mb-6">
                <li className="flex items-center gap-2 text-gray-300">
                  <span className="text-green-400">✓</span> Everything in Pro
                </li>
                <li className="flex items-center gap-2 text-gray-300">
                  <span className="text-green-400">✓</span> 10 team members
                </li>
                <li className="flex items-center gap-2 text-gray-300">
                  <span className="text-green-400">✓</span> API access
                </li>
                <li className="flex items-center gap-2 text-gray-300">
                  <span className="text-green-400">✓</span> Custom branding
                </li>
              </ul>
              <button className="w-full py-3 rounded-lg bg-white/10 hover:bg-white/20 text-white font-medium transition-all">
                Contact Sales
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 border-t border-white/10">
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-gray-500">
            © 2024 ContentAI. Built for creators in Southeast Asia & Middle East.
          </p>
        </div>
      </footer>
    </main>
  )
}

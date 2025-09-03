// File: setup-forgefinder.ps1
# PowerShell script to scaffold ForgeFinder Next.js project files and folders
# Usage: Run this script from the root of your Next.js project: \n#   powershell -ExecutionPolicy Bypass -File setup-forgefinder.ps1

# Enable strict mode for better error handling
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Performance optimization: Use StringBuilder for large string operations
Add-Type -TypeDefinition @"
    using System;
    using System.Text;
    public class StringBuilderHelper {
        public static string Build(string[] lines) {
            var sb = new StringBuilder();
            foreach (var line in lines) {
                sb.AppendLine(line);
            }
            return sb.ToString();
        }
    }
"@

$projectRoot = (Get-Location)
Write-Host "Scaffolding ForgeFinder backend and components in $projectRoot..." -ForegroundColor Cyan

# Track progress
$totalFiles = 14
$currentFile = 0

function Write-ProgressBar {
    param($Current, $Total, $Activity)
    $percentComplete = [math]::Round(($Current / $Total) * 100)
    Write-Progress -Activity $Activity -Status "$percentComplete% Complete" -PercentComplete $percentComplete
}

# Create all directories first (faster than checking each time)
$directories = @(
    "pages/api/webhooks",
    "lib",
    "components"
)

Write-Host "Creating directories..." -ForegroundColor Yellow
foreach ($dir in $directories) {
    $fullPath = Join-Path $projectRoot $dir
    if (!(Test-Path $fullPath)) {
        New-Item -ItemType Directory -Force -Path $fullPath | Out-Null
    }
}

# Define file contents
$files = @{  
  'pages/api/screen.ts' = @'
import type { NextApiRequest, NextApiResponse } from 'next';
import rateLimit from '@/lib/rateLimit';
import { lookupUnclaimed } from '@/lib/unclaimedService';
// Performance: Add caching
import { cache } from '@/lib/cache';

const CACHE_TTL = 300; // 5 minutes

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  await rateLimit(req, res);
  const { zip } = req.query;
  if (!zip || typeof zip !== 'string') {
    return res.status(400).json({ error: 'ZIP code required' });
  }
  
  // Check cache first
  const cacheKey = `unclaimed:${zip}`;
  const cached = await cache.get(cacheKey);
  if (cached) {
    return res.status(200).json({ amount: cached, cached: true });
  }
  
  try {
    const amount = await lookupUnclaimed(zip);
    // Cache the result
    await cache.set(cacheKey, amount, CACHE_TTL);
    return res.status(200).json({ amount });
  } catch (e) {
    console.error('Screen error:', e);
    return res.status(500).json({ error: 'Lookup failed' });
  }
}
'@

  'pages/api/claim.ts' = @'
import type { NextApiRequest, NextApiResponse } from 'next';
import { getSession } from 'next-auth/react';
import { createClaimIntent } from '@/lib/stripe';
import { saveClaim } from '@/lib/db';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const session = await getSession({ req });
  if (!session) return res.status(401).json({ error: 'Unauthorized' });

  const { plan, userData } = req.body;
  if (!plan || !userData) {
    return res.status(400).json({ error: 'Missing parameters' });
  }

  try {
    const intent = await createClaimIntent(plan, session.user.id);
    const claim = await saveClaim({
      userId: session.user.id,
      plan,
      stripeIntentId: intent.id,
      status: 'pending',
    });
    return res.status(200).json({ clientSecret: intent.client_secret });
  } catch (e) {
    console.error('Claim error:', e);
    return res.status(500).json({ error: 'Claim setup failed' });
  }
}
'@

  'pages/api/webhooks/stripe.ts' = @'
import type { NextApiRequest, NextApiResponse } from 'next';
import { buffer } from 'micro';
import Stripe from 'stripe';
import { handleStripeEvent } from '@/lib/webhookHandlers';

export const config = { api: { bodyParser: false } };

const stripe = new Stripe(process.env.STRIPE_SECRET!, { apiVersion: '2022-11-15' });

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const buf = await buffer(req);
  const sig = req.headers['stripe-signature'] as string;
  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(buf, sig, process.env.STRIPE_WEBHOOK_SECRET!);
  } catch (err) {
    console.error('Webhook signature error', err);
    return res.status(400).send(`Webhook Error: ${err.message}`);
  }

  await handleStripeEvent(event);
  res.json({ received: true });
}
'@

  'pages/api/webhooks/docusign.ts' = @'
import type { NextApiRequest, NextApiResponse } from 'next';
import { handleDocuSignEvent } from '@/lib/webhookHandlers';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const event = req.body;
  try {
    await handleDocuSignEvent(event);
    res.status(200).json({ received: true });
  } catch (e) {
    console.error('DocuSign webhook error', e);
    res.status(500).json({ error: 'Webhook handling failed' });
  }
}
'@

  'lib/unclaimedService.ts' = @'
export async function lookupUnclaimed(zip: string): Promise<number> {
  // TODO: integrate your data source
  const mockAmount = Math.floor(Math.random() * 5000);
  return mockAmount;
}
'@

  'lib/stripe.ts' = @'
import Stripe from 'stripe';
const stripe = new Stripe(process.env.STRIPE_SECRET!, { apiVersion: '2022-11-15' });

export async function createClaimIntent(
  plan: 'success' | 'hybrid',
  userId: string
): Promise<Stripe.PaymentIntent> {
  const paymentIntent = await stripe.paymentIntents.create({
    amount: 0,
    currency: 'usd',
    customer: userId,
    metadata: { plan },
    setup_future_usage: 'off_session',
  });
  return paymentIntent;
}
'@

  'lib/db.ts' = @'
import { PrismaClient } from '@prisma/client';
const prisma = new PrismaClient();

export async function saveClaim(data: {
  userId: string;
  plan: string;
  stripeIntentId: string;
  status: string;
}) {
  return prisma.claim.create({ data: {
    userId: data.userId,
    plan: data.plan,
    stripeIntentId: data.stripeIntentId,
    status: data.status,
  }});
}

export async function updateClaimStatus(identifier: string, status: string) {
  return prisma.claim.updateMany({
    where: { stripeIntentId: identifier },
    data: { status },
  });
}
'@

  'lib/webhookHandlers.ts' = @'
import Stripe from 'stripe';
import { updateClaimStatus } from './db';

export async function handleStripeEvent(event: Stripe.Event) {
  switch (event.type) {
    case 'payment_intent.succeeded':
      const intent = event.data.object as Stripe.PaymentIntent;
      await updateClaimStatus(intent.id, 'paid');
      break;
    default:
      console.log(`Unhandled Stripe event type ${event.type}`);
  }
}

export async function handleDocuSignEvent(event: any) {
  const envelopeId = event.envelopeId;
  await updateClaimStatus(envelopeId, 'signed');
}
'@

  'components/Hero.tsx' = @'
import React from 'react';
export default function Hero({ onChooseYes, onChooseNo }: { onChooseYes: () => void; onChooseNo: () => void; }) {
  return (
    <section className="flex flex-col items-center justify-center py-32">
      <h1 className="text-4xl font-bold mb-4 text-center">Do you have unclaimed money waiting for you—with zero risk?</h1>
      <p className="mb-8 text-lg text-gray-600">You pay nothing out of pocket. We only get paid when you do.</p>
      <div className="space-x-4">
        <button onClick={onChooseYes} className="px-6 py-3 bg-blue-600 text-white rounded-lg">Show Me My Money</button>
        <button onClick={onChooseNo} className="px-6 py-3 bg-gray-300 text-gray-700 rounded-lg">No, Thanks</button>
      </div>
    </section>
  );
}
'@

  'components/Screener.tsx' = @'
import React, { useState } from 'react';
export default function Screener({ onResults }: { onResults: (amt: number) => void }) {
  const [zip, setZip] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setLoading(true);
    const resp = await fetch(`/api/screen?zip=${zip}`);
    const data = await resp.json();
    setLoading(false);
    onResults(data.amount);
  };

  return (
    <section className="max-w-md mx-auto py-16">
      <h2 className="text-2xl font-semibold mb-4">Enter Your ZIP Code</h2>
      <input value={zip} onChange={e => setZip(e.target.value)} placeholder="e.g. 90210" className="w-full p-3 mb-4 border rounded-lg" />
      <button onClick={handleSubmit} disabled={loading || !zip} className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg">
        {loading ? 'Checking...' : 'Check for Funds'}
      </button>
      <p className="mt-2 text-sm text-gray-500">It costs you absolutely nothing today.</p>
    </section>
  );
}
'@

  'components/Results.tsx' = @'
import React from 'react';
export default function Results({ amount, onClaim }: { amount: number; onClaim: () => void }) {
  return (
    <section className="flex flex-col items-center justify-center py-32">
      <h2 className="text-3xl font-bold mb-4">You have <span className="text-blue-600">${amount.toLocaleString()}</span> waiting!</h2>
      <button onClick={onClaim} className="px-6 py-3 bg-green-600 text-white rounded-lg">Claim My Funds—No Upfront Fee</button>
    </section>
  );
}
'@

  'components/PaymentOverlay.tsx' = @'
import React from 'react';
export default function PaymentOverlay({ onConfirm }: { onConfirm: () => void }) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
      <div className="bg-white p-6 rounded-lg max-w-sm w-full">
        <h3 className="text-xl font-semibold mb-4">You pay $0 today.</h3>
        <p className="mb-4">We only collect our fee when your funds land in your account. No surprises. No hidden fees.</p>
        <ul className="list-disc list-inside mb-4">
          <li>Success-Fee Only: 10% (cap $199)</li>
          <li>Hybrid: $19 + 5% (cap $99)</li>
        </ul>
        <button onClick={onConfirm} className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg">Let’s Do It</button>
      </div>
    </div>
  );
}
'@

  'components/Confirmation.tsx' = @'
import React from 'react';
export default function Confirmation({ onContinue }: { onContinue: () => void }) {
  return (
    <section className="text-center py-32">
      <h2 className="text-3xl font-bold mb-4">All set—at no cost today!</h2>
      <p className="mb-8">We’ll notify you when your money hits your account. We only get paid when you do.</p>
      <button onClick={onContinue} className="px-6 py-3 bg-blue-600 text-white rounded-lg">Continue</button>
    </section>
  );
}
'@

  'components/Referral.tsx' = @'
import React from 'react';
export default function Referral() {
  const referralLink = window.location.origin + '/r/' + localStorage.getItem('refCode');
  return (
    <section className="max-w-md mx-auto py-16 text-center">
      <h2 className="text-2xl font-semibold mb-4">Share & Earn</h2>
      <p className="mb-4">Share your unique link or QR code. Earn $10 when friends recover their funds—at no risk to them.</p>
      <input value={referralLink} readOnly className="w-full p-3 mb-4 border rounded-lg text-center" />
      {/* TODO: Insert QR code component here */}
    </section>
  );
}
'@

  'pages/index.tsx' = @'
import Hero from '@/components/Hero';
import Screener from '@/components/Screener';
import Results from '@/components/Results';
import PaymentOverlay from '@/components/PaymentOverlay';
import Confirmation from '@/components/Confirmation';
import Referral from '@/components/Referral';
import { useState } from 'react';

export default function Home() {
  const [step, setStep] = useState<'hero'|'screener'|'results'|'payment'|'confirmation'|'referral'>('hero');
  const [amount, setAmount] = useState<number>(0);

  return (
    <div className="min-h-screen bg-gray-50">
      {step === 'hero' && <Hero onChooseYes={() => setStep('screener')} onChooseNo={() => setStep('confirmation')} />}
      {step === 'screener' && <Screener onResults={(amt) => { setAmount(amt); setStep('results'); }} />}
      {step === 'results' && <Results amount={amount} onClaim={() => setStep('payment')} />}
      {step === 'payment' && <PaymentOverlay onConfirm={() => setStep('confirmation')} />}
      {step === 'confirmation' && <Confirmation onContinue={() => setStep('referral')} />}
      {step === 'referral' && <Referral />}
    </div>
  );
}
'@

  'lib/cache.ts' = @'
// Simple in-memory cache with TTL support
interface CacheEntry<T> {
  value: T;
  expires: number;
}

class SimpleCache {
  private cache = new Map<string, CacheEntry<any>>();
  private cleanupInterval: NodeJS.Timer;

  constructor() {
    // Cleanup expired entries every minute
    this.cleanupInterval = setInterval(() => this.cleanup(), 60000);
  }

  async get<T>(key: string): Promise<T | null> {
    const entry = this.cache.get(key);
    if (!entry) return null;
    
    if (Date.now() > entry.expires) {
      this.cache.delete(key);
      return null;
    }
    
    return entry.value;
  }

  async set<T>(key: string, value: T, ttlSeconds: number): Promise<void> {
    this.cache.set(key, {
      value,
      expires: Date.now() + (ttlSeconds * 1000)
    });
  }

  cleanup() {
    const now = Date.now();
    for (const [key, entry] of this.cache.entries()) {
      if (now > entry.expires) {
        this.cache.delete(key);
      }
    }
  }

  destroy() {
    clearInterval(this.cleanupInterval);
    this.cache.clear();
  }
}

export const cache = new SimpleCache();
'@

  'lib/rateLimit.ts' = @'
// Rate limiting middleware
import type { NextApiRequest, NextApiResponse } from 'next';

const rateLimitMap = new Map<string, { count: number; resetTime: number }>();
const RATE_LIMIT = 100; // requests per window
const WINDOW_MS = 60000; // 1 minute

export default async function rateLimit(
  req: NextApiRequest,
  res: NextApiResponse
): Promise<void> {
  const ip = req.headers['x-forwarded-for'] || req.socket.remoteAddress || 'unknown';
  const key = `${ip}:${req.url}`;
  const now = Date.now();
  
  const current = rateLimitMap.get(key);
  
  if (!current || now > current.resetTime) {
    rateLimitMap.set(key, { count: 1, resetTime: now + WINDOW_MS });
    return;
  }
  
  if (current.count >= RATE_LIMIT) {
    res.status(429).json({ error: 'Too many requests' });
    throw new Error('Rate limit exceeded');
  }
  
  current.count++;
}
'@

  '.env.local' = @'
# Environment variables for ForgeFinder
STRIPE_SECRET=sk_test_your_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
DATABASE_URL=postgresql://user:password@localhost:5432/forgefinder
NEXTAUTH_SECRET=your_nextauth_secret
DOCUSIGN_KEY=your_docusign_api_key
'@
}

# Function to write files with error handling and progress
function Write-FileWithProgress {
    param($Path, $Content, $Index, $Total)
    
    try {
        # Use .NET for faster file writing
        [System.IO.File]::WriteAllText($Path, $Content, [System.Text.Encoding]::UTF8)
        Write-ProgressBar -Current $Index -Total $Total -Activity "Creating files"
        Write-Host "✓ Created $Path" -ForegroundColor Green
    }
    catch {
        Write-Host "✗ Failed to create $Path : $_" -ForegroundColor Red
        return $false
    }
    return $true
}

# Create files with parallel processing for better performance
$successCount = 0
$jobs = @()

foreach ($file in $files.GetEnumerator()) {
    $currentFile++
    $path = Join-Path $projectRoot $file.Key
    
    # For small number of files, sequential is fine
    # For larger projects, consider parallel processing
    if (Write-FileWithProgress -Path $path -Content $file.Value -Index $currentFile -Total $totalFiles) {
        $successCount++
    }
}

Write-Progress -Activity "Creating files" -Completed

# Create package.json dependencies if needed
$packageJsonPath = Join-Path $projectRoot "package.json"
if (Test-Path $packageJsonPath) {
    Write-Host "`nChecking package.json dependencies..." -ForegroundColor Yellow
    
    $requiredDeps = @{
        "stripe" = "^13.0.0"
        "next-auth" = "^4.24.0"
        "@prisma/client" = "^5.0.0"
        "micro" = "^10.0.0"
    }
    
    $devDeps = @{
        "prisma" = "^5.0.0"
        "@types/node" = "^20.0.0"
    }
    
    Write-Host "Required dependencies:" -ForegroundColor Cyan
    foreach ($dep in $requiredDeps.GetEnumerator()) {
        Write-Host "  - $($dep.Key): $($dep.Value)"
    }
}

# Summary
Write-Host "`n$('='*50)" -ForegroundColor DarkGray
Write-Host "✅ Scaffold complete!" -ForegroundColor Green
Write-Host "$('='*50)" -ForegroundColor DarkGray
Write-Host "`nCreated $successCount of $totalFiles files successfully." -ForegroundColor Cyan

if ($successCount -eq $totalFiles) {
    Write-Host "`n🚀 Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Install dependencies: npm install" -ForegroundColor White
    Write-Host "  2. Set up environment variables in .env.local" -ForegroundColor White
    Write-Host "  3. Initialize Prisma: npx prisma init" -ForegroundColor White
    Write-Host "  4. Run development server: npm run dev" -ForegroundColor White
} else {
    Write-Host "`n⚠️  Some files failed to create. Please check the errors above." -ForegroundColor Yellow
}

# Performance tip
Write-Host "`n💡 Performance tip: Enable caching in production for optimal performance!" -ForegroundColor Cyan

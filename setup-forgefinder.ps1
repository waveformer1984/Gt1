// File: setup-forgefinder.ps1
# PowerShell script to scaffold ForgeFinder Next.js project files and folders
# Usage: Run this script from the root of your Next.js project: \n#   powershell -ExecutionPolicy Bypass -File setup-forgefinder.ps1

$projectRoot = (Get-Location)
Write-Host "Scaffolding ForgeFinder backend and components in $projectRoot..."

# Define file contents
$files = @{  
  'pages/api/screen.ts' = @'
import type { NextApiRequest, NextApiResponse } from 'next';
import rateLimit from '@/lib/rateLimit';
import { lookupUnclaimed } from '@/lib/unclaimedService';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  await rateLimit(req, res);
  const { zip } = req.query;
  if (!zip || typeof zip !== 'string') {
    return res.status(400).json({ error: 'ZIP code required' });
  }
  try {
    const amount = await lookupUnclaimed(zip);
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

  '.env.local' = @'
# Environment variables for ForgeFinder
STRIPE_SECRET=sk_test_your_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
DATABASE_URL=postgresql://user:password@localhost:5432/forgefinder
NEXTAUTH_SECRET=your_nextauth_secret
DOCUSIGN_KEY=your_docusign_api_key
'@
}

# Create directories and write files
foreach ($file in $files.GetEnumerator()) {
  $path = Join-Path $projectRoot $file.Key
  $dir = Split-Path $path
  if (!(Test-Path $dir)) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
  }
  Set-Content -Path $path -Value $file.Value -Force -Encoding UTF8
  Write-Host "Created $path"
}

Write-Host "Scaffold complete. Run 'npm install' then 'npm run dev' to start your app."

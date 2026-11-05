const SIGNUP = 'https://3.basecamp.com/signup/account/new?plan=one_v1'

const nav = [
  ['How it works', '/how-it-works'],
  ['Before & after', '/before-and-after'],
  ['Got clients?', '/features/clients'],
  ['Pricing', '/pricing'],
  ['Support', '/support'],
]

const reviews = ['extremely user friendly', 'perfect solution for remote teams', 'truly amazing!']

const testimonials = [
  ['I’ve used Basecamp for a million projects over the last decade and a half. It\'s beautiful software that has resisted every wrong trend and stayed true to the things that mattered most. Highly recommended.', 'Tobi Lütke, CEO, Shopify'],
  ['We can see exactly what needs to be done and when. We\'re much more efficient.', 'Tina Lannin, 121 Captions'],
  ['We\'ve had less confusion with task responsibilities and deadlines, which has increased productivity and efficiency.', 'Dale Lavine, NASA'],
  ['Accountability for tasks. No more ‘I thought so and so was responsible for that.’', 'George Groves, Piehole.TV'],
  ['We are all collaborating more on feedback, it helps to show accountability as well.', 'Samantha Silberberg, Quartz'],
  ['We don\'t need to spend as much time in meetings now that we use Basecamp.', 'Brad Vandiviere, Faith Chapel Billings'],
  ['Transparency and communication has increased.', 'Joey Rosenberg, Women Who Code'],
  ['Time management and productivity. Makes my job easier rather than having to constantly ask for progress updates.', 'Kyle Jernigan, Crossroads Church'],
  ['Greater collaboration and less Excel!', 'Spencer Stevenson, 3M'],
  ['Task completion! The lists and reminders help people remember what they said they were going to do and helps hold them accountable to the team.', 'Scot Evans, University of Miami'],
]

const footer = [
  ['Basecamp apps', [['iOS, Android, Mac, and PC', '/via'], ['integrations', '/extras']]],
  ['Company', [['about us', '/about'], ['podcast', 'https://rework.fm/'], ['blog', 'https://signalvnoise.com/'], ['books', '/books'], ['handbook', '/handbook'], ['newsletter', '/newsletter']]],
  ['Guides', [['going remote', '/remote-resources'], ['team communication', '/guides/how-we-communicate'], ['group chat: group stress', '/guides/group-chat-problems']]],
  ['Our new app', [['HEY - email at its best', 'https://hey.com']]],
  ['Fine print', [['customer rights', '/rights'], ['privacy & terms', '/about/policies'], ['uptime', '/uptime/bc3'], ['system status', '/status']]],
]

const Cta = () => (
  <div className="flex flex-col items-center gap-4">
    <a href="/pricing" className="rounded-full bg-ink px-8 py-4 text-lg font-bold text-white shadow-lg transition hover:-translate-y-0.5 hover:bg-black focus:outline-none focus:ring-4 focus:ring-sun">
      Give Basecamp a Try
    </a>
    <p className="text-sm font-medium text-ink/70">4,000 companies signed up in the last week alone!</p>
  </div>
)

const Stars = () => <img src="/images/stars.svg" alt="5 stars" className="h-5 w-auto" />

export default function App() {
  return (
    <div>
      <header className="sticky top-0 z-20 border-b border-ink/10 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-3">
          <a href="/"><img src="/images/basecamp-logo.svg" alt="Basecamp logo" className="h-9 w-auto" /></a>
          <nav className="hidden items-center gap-6 text-sm font-medium lg:flex">
            {nav.map(([l, h]) => <a key={h} href={h} className="hover:underline">{l}</a>)}
            <a href="https://launchpad.37signals.com/signin" className="hover:underline">Sign in</a>
          </nav>
          <a href={SIGNUP} className="rounded-full bg-sun px-5 py-2 text-sm font-bold text-ink transition hover:brightness-95">Try it FREE</a>
        </div>
        <nav className="flex gap-5 overflow-x-auto border-t border-ink/10 px-5 py-2 text-sm font-medium lg:hidden">
          {nav.map(([l, h]) => <a key={h} href={h} className="whitespace-nowrap">{l}</a>)}
          <a href="https://launchpad.37signals.com/signin" className="whitespace-nowrap">Sign in</a>
        </nav>
      </header>

      <main>
        <section className="bg-cream px-5 pb-20 pt-14 text-center">
          <div className="mx-auto grid max-w-4xl gap-3 sm:grid-cols-3">
            {reviews.map((r) => (
              <figure key={r} className="rounded-2xl bg-white p-4 shadow-sm ring-1 ring-ink/5">
                <div className="flex justify-center"><Stars /></div>
                <blockquote className="mt-2 text-sm font-medium">“{r}”</blockquote>
              </figure>
            ))}
          </div>
          <h1 className="mx-auto mt-14 max-w-4xl text-4xl font-black leading-tight tracking-tight sm:text-6xl">
            The All-In-One Toolkit for Working Remotely.
          </h1>
          <div className="mx-auto mt-8 grid max-w-3xl gap-4 text-left sm:grid-cols-2">
            <p className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-ink/5">
              <strong className="block text-red-700">Before Basecamp:</strong>
              Projects feel scattered, things slip, it’s tough to see where things stand, and people are stressed.
            </p>
            <p className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-ink/5">
              <strong className="block text-leaf">After Basecamp:</strong>
              Everything’s organized in one place, you’re on top of things, progress is clear, and a sense of calm sets in.
            </p>
          </div>
          <div className="mt-10"><Cta /></div>
        </section>

        <section className="px-5 py-20">
          <div className="mx-auto grid max-w-6xl items-center gap-12 lg:grid-cols-2">
            <div className="relative mx-auto w-full max-w-lg">
              <picture>
                <source media="(max-width: 639px)" srcSet="/images/project-remote-small.png" />
                <img src="/images/project-remote-large.png" alt="here's what a Basecamp project looks like" className="w-full rounded-2xl shadow-2xl ring-1 ring-ink/10" />
              </picture>
              <img src="/images/project-hero-captions.png" alt="" aria-hidden="true" className="pointer-events-none absolute inset-0 h-full w-full object-contain" />
            </div>
            <div>
              <h2 className="text-3xl font-black tracking-tight sm:text-4xl">One place, not all over the place.</h2>
              <p className="mt-6 text-lg leading-relaxed"><strong>Remote work is especially challenging when</strong> stuff’s spread out across emails, file services, task managers, spreadsheets, chats, meetings, etc. Things get lost, you don’t know where to look for stuff, and people put the right information in the wrong place.</p>
              <p className="mt-4 text-lg leading-relaxed"><strong>But when it’s all together in Basecamp, you’ll see</strong> where everything is, understand what everyone’s working on, and know exactly where to put the next thing everyone needs to know about. Your team can access Basecamp from anywhere - on the web, on iOS, and Android. This is the modern way – The Basecamp Way to Work.</p>
              <a href="/how-it-works" className="mt-6 inline-block font-bold underline decoration-sun decoration-4 underline-offset-4 hover:bg-sun/40">Basecamp is different – take a deeper look at how it works &gt;</a>
            </div>
          </div>
        </section>

        <section className="bg-sun/30 px-5 py-20">
          <div className="mx-auto grid max-w-4xl items-center gap-10 md:grid-cols-[240px_1fr]">
            <a href="/books/remote" className="mx-auto block w-48 md:w-full"><img src="/images/remote-cover.png" alt="REMOTE cover" className="w-full rounded shadow-xl transition hover:-rotate-2" /></a>
            <div>
              <h2 className="text-3xl font-black tracking-tight sm:text-4xl">We literally wrote the book on working remotely.</h2>
              <p className="mt-5 text-lg leading-relaxed">We don't just make software for remote work; we wrote a popular and influential book about working remotely too. <strong>REMOTE</strong> shows both employers and employees how they can work together, remotely, from any desk, in any place, anytime, anywhere. Avoid common pitfalls, learn best practices, and get up to speed <em>quick</em>.</p>
              <a href="/books/remote" className="mt-6 inline-block rounded-full bg-ink px-6 py-3 font-bold text-white hover:bg-black">learn more about REMOTE</a>
            </div>
          </div>
        </section>

        <section className="px-5 py-20">
          <div className="mx-auto max-w-6xl">
            <h2 className="mx-auto max-w-3xl text-center text-3xl font-black tracking-tight sm:text-4xl">Companies change for the better when they work in Basecamp.</h2>
            <p className="mx-auto mt-5 max-w-3xl text-center text-lg">Software development shops, design firms, freelancers, consultants, architects, agencies, media companies, schools, and non-profits around the world have switched to Basecamp to <strong>fundamentally improve</strong> their project workflow.</p>
            <div className="mt-12 columns-1 gap-5 md:columns-2 lg:columns-3">
              {testimonials.map(([q, a], i) => (
                <figure key={a} className={`mb-5 break-inside-avoid rounded-2xl p-6 ring-1 ring-ink/10 ${i === 0 ? 'bg-sun/40' : 'bg-cream'}`}>
                  <blockquote className={i === 0 ? 'text-lg font-medium' : ''}>“{q}”</blockquote>
                  <figcaption className="mt-3 text-sm font-bold">— {a}</figcaption>
                </figure>
              ))}
            </div>
            <p className="mt-6 text-center"><a href="/customers" className="font-bold underline decoration-sun decoration-4 underline-offset-4">Hear from hundreds more customers about what's changed for the better since they made the switch to Basecamp &gt;</a></p>
          </div>
        </section>

        <section className="bg-cream px-5 py-20 text-center">
          <p className="mb-8 text-xl font-bold">Have questions? <a href="/support" className="underline decoration-sun decoration-4">Holler</a>. Ready to get going? Engage:</p>
          <Cta />
        </section>
      </main>

      <footer className="bg-ink px-5 py-12 text-sm text-white/80">
        <div className="mx-auto max-w-6xl space-y-3">
          {footer.map(([t, links]) => (
            <p key={t}><strong className="text-white">{t}:</strong>{' '}
              {links.map(([l, h], i) => <span key={h}><a href={h} className="underline hover:text-sun">{l}</a>{i < links.length - 1 ? ', ' : '.'} </span>)}
            </p>
          ))}
          <p className="pt-6 italic text-white/60">Copyright ©1999-2021 Basecamp. All rights reserved. Enjoy the rest of your day!</p>
        </div>
      </footer>
    </div>
  )
}

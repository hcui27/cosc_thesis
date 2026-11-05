const nav = [['How it works','/how-it-works'],['Before & after','/before-and-after'],['Got clients?','/features/clients'],['Pricing','/pricing'],['Support','/support']]
const reviews = ['extremely user friendly','perfect solution for remote teams','truly amazing!']
const quotes = [
['I’ve used Basecamp for a million projects over the last decade and a half. It\'s beautiful software that has resisted every wrong trend and stayed true to the things that mattered most. Highly recommended.','Tobi Lütke, CEO, Shopify'],
['We can see exactly what needs to be done and when. We\'re much more efficient.','Tina Lannin, 121 Captions'],
['We\'ve had less confusion with task responsibilities and deadlines, which has increased productivity and efficiency.','Dale Lavine, NASA'],
['Accountability for tasks. No more ‘I thought so and so was responsible for that.’','George Groves, Piehole.TV'],
['We are all collaborating more on feedback, it helps to show accountability as well.','Samantha Silberberg, Quartz'],
['We don\'t need to spend as much time in meetings now that we use Basecamp.','Brad Vandiviere, Faith Chapel Billings'],
['Transparency and communication has increased.','Joey Rosenberg, Women Who Code'],
['Time management and productivity. Makes my job easier rather than having to constantly ask for progress updates.','Kyle Jernigan, Crossroads Church'],
['Greater collaboration and less Excel!','Spencer Stevenson, 3M'],
['Task completion! The lists and reminders help people remember what they said they were going to do and helps hold them accountable to the team.','Scot Evans, University of Miami'],
]
const footer = [
['Basecamp apps',[['iOS, Android, Mac, and PC','/via'],['integrations','/extras']]],
['Company',[['about us','/about'],['podcast','https://rework.fm/'],['blog','https://signalvnoise.com/'],['books','/books'],['handbook','/handbook'],['newsletter','/newsletter']]],
['Guides',[['going remote','/remote-resources'],['team communication','/guides/how-we-communicate'],['group chat: group stress','/guides/group-chat-problems']]],
['Our new app',[['HEY - email at its best','https://hey.com']]],
['Fine print',[['customer rights','/rights'],['privacy & terms','/about/policies'],['uptime','/uptime/bc3'],['system status','/status']]],
]
const Cta = () => (
  <div className="text-center">
    <a href="/pricing" className="inline-block rounded-full bg-bc-green px-8 py-4 text-lg font-bold text-white shadow-lg transition hover:-translate-y-0.5 hover:bg-emerald-800">Give Basecamp a Try</a>
    <p className="mt-4 text-sm font-medium text-bc-dark/70">4,000 companies signed up in the last week alone!</p>
  </div>
)
const H2 = ({children}) => <h2 className="text-3xl font-extrabold leading-tight sm:text-4xl md:text-5xl">{children}</h2>

export default function App() {
  return (
    <div>
      <header className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-5 py-5">
        <a href="/"><img src="/images/basecamp-logo.svg" alt="Basecamp logo" className="h-9"/></a>
        <nav className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm font-semibold">
          {nav.map(([t,h]) => <a key={t} href={h} className="hover:underline">{t}</a>)}
          <a href="https://launchpad.37signals.com/signin" className="hover:underline">Sign in</a>
          <a href="https://3.basecamp.com/signup/account/new?plan=one_v1" className="rounded-full bg-bc-green px-4 py-2 text-white hover:bg-emerald-800">Try it FREE</a>
        </nav>
      </header>

      <section className="mx-auto max-w-4xl px-5 pb-16 pt-8 text-center">
        <ul className="mb-10 grid gap-4 sm:grid-cols-3">
          {reviews.map(r => (
            <li key={r} className="flex flex-col items-center gap-2">
              <img src="/images/stars.svg" alt="5 stars" className="h-5"/>
              <span className="font-semibold italic">“{r}”</span>
            </li>))}
        </ul>
        <h1 className="text-4xl font-extrabold leading-tight sm:text-5xl md:text-6xl">The All-In-One Toolkit for Working Remotely.</h1>
        <p className="mx-auto mt-6 max-w-3xl text-lg leading-relaxed md:text-xl">
          <strong>Before Basecamp:</strong> Projects feel scattered, things slip, it’s tough to see where things stand, and people are stressed. <strong>After Basecamp:</strong> Everything’s organized in one place, you’re on top of things, progress is clear, and a sense of calm sets in.
        </p>
        <div className="mt-8"><Cta/></div>
      </section>

      <section className="bg-white py-16">
        <div className="mx-auto grid max-w-6xl items-center gap-10 px-5 md:grid-cols-2">
          <div className="relative mx-auto w-full max-w-md">
            <picture>
              <source media="(max-width: 639px)" srcSet="/images/project-remote-small.png"/>
              <img src="/images/project-remote-large.png" alt="here's what a Basecamp project looks like" className="w-full rounded-xl shadow-2xl"/>
            </picture>
            <img src="/images/project-hero-captions.png" alt="" aria-hidden="true" className="pointer-events-none absolute inset-0 hidden h-full w-full object-contain md:block md:scale-110"/>
          </div>
          <div>
            <H2>One place, not all over the place.</H2>
            <p className="mt-6 text-lg leading-relaxed"><strong>Remote work is especially challenging when</strong> stuff’s spread out across emails, file services, task managers, spreadsheets, chats, meetings, etc. Things get lost, you don’t know where to look for stuff, and people put the right information in the wrong place.</p>
            <p className="mt-4 text-lg leading-relaxed"><strong>But when it’s all together in Basecamp, you’ll see</strong> where everything is, understand what everyone’s working on, and know exactly where to put the next thing everyone needs to know about. Your team can access Basecamp from anywhere - on the web, on iOS, and Android. This is the modern way – The Basecamp Way to Work.</p>
            <a href="/how-it-works" className="mt-6 inline-block font-bold text-bc-green underline underline-offset-4">Basecamp is different – take a deeper look at how it works &gt;</a>
          </div>
        </div>
      </section>

      <section className="mx-auto grid max-w-5xl items-center gap-10 px-5 py-20 md:grid-cols-[260px_1fr]">
        <a href="/books/remote" className="mx-auto"><img src="/images/remote-cover.png" alt="REMOTE cover" className="w-56 rotate-[-3deg] rounded shadow-2xl transition hover:rotate-0 md:w-full"/></a>
        <div>
          <H2>We literally wrote the book on working remotely.</H2>
          <p className="mt-6 text-lg leading-relaxed">We don't just make software for remote work; we wrote a popular and influential book about working remotely too. <strong>REMOTE</strong> shows both employers and employees how they can work together, remotely, from any desk, in any place, anytime, anywhere. Avoid common pitfalls, learn best practices, and get up to speed <em>quick</em>.</p>
          <a href="/books/remote" className="mt-6 inline-block font-bold text-bc-green underline underline-offset-4">learn more about REMOTE</a>
        </div>
      </section>

      <section className="bg-bc-green/10 py-20">
        <div className="mx-auto max-w-6xl px-5">
          <div className="mx-auto max-w-3xl text-center">
            <H2>Companies change for the better when they work in Basecamp.</H2>
            <p className="mt-6 text-lg leading-relaxed">Software development shops, design firms, freelancers, consultants, architects, agencies, media companies, schools, and non-profits around the world have switched to Basecamp to <strong>fundamentally improve</strong> their project workflow.</p>
          </div>
          <div className="mt-12 columns-1 gap-6 md:columns-2 lg:columns-3">
            {quotes.map(([q,a],i) => (
              <figure key={a} className={`mb-6 break-inside-avoid rounded-2xl bg-white p-6 shadow ${i===0?'lg:border-2 lg:border-bc-green':''}`}>
                <blockquote className="leading-relaxed">“{q}”</blockquote>
                <figcaption className="mt-4 text-sm font-bold text-bc-green">— {a}</figcaption>
              </figure>))}
          </div>
          <p className="mt-6 text-center"><a href="/customers" className="font-bold text-bc-green underline underline-offset-4">Hear from hundreds more customers about what's changed for the better since they made the switch to Basecamp &gt;</a></p>
          <p className="mt-14 text-center text-xl font-bold">Have questions? <a href="/support" className="underline">Holler</a>. Ready to get going? Engage:</p>
          <div className="mt-6"><Cta/></div>
        </div>
      </section>

      <footer className="relative overflow-hidden bg-bc-dark text-white">
        <img src="/images/footer-graph.png" alt="" aria-hidden="true" className="pointer-events-none absolute bottom-0 right-0 w-full max-w-3xl opacity-60"/>
        <div className="relative mx-auto max-w-6xl space-y-3 px-5 py-14 text-sm leading-relaxed">
          {footer.map(([label, links]) => (
            <p key={label}><strong>{label}:</strong>{' '}
              {links.map(([t,h],i) => <span key={t}><a href={h} className="underline underline-offset-2 hover:text-bc-yellow">{t}</a>{i<links.length-1?', ':'.'}</span>)}
            </p>))}
          <p className="pt-6 italic text-white/70">Copyright ©1999-2021 Basecamp. All rights reserved. Enjoy the rest of your day!</p>
        </div>
      </footer>
    </div>
  )
}

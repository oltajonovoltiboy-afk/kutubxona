(()=>{
 const form=document.getElementById('online-search-form');if(!form)return;
 const input=document.getElementById('online-search-query'),status=document.getElementById('online-search-status'),grid=document.getElementById('online-search-results');
 const esc=s=>String(s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const runSearch=async e=>{if(e)e.preventDefault();const q=input.value.trim();if(q.length<2)return;status.textContent='Ziyouz, Open Library va Google Books bazalari tekshirilmoqda…';grid.innerHTML='';
  try{const response=await fetch('/api/online-search/?q='+encodeURIComponent(q),{headers:{'Accept':'application/json'}});if(!response.ok)throw new Error('Qidiruv serveri javob bermadi');const data=await response.json(),items=data.results||[];status.textContent=`${items.length} ta natija topildi. Manbalar: ${(data.providers||[]).join(', ')||'hozircha javob bermadi'}.`;
   if(!items.length){grid.innerHTML='<div class="empty"><h3>Kitob topilmadi</h3><p>Boshqa nom, muallif yoki qisqaroq so‘z bilan qidirib ko‘ring.</p></div>';return;}
   grid.innerHTML=items.map(b=>{const pdf=b.pdf||'',embed=b.read_url||b.url||'',reader=window.onlineReaderUrl+'?'+(pdf?'url='+encodeURIComponent(pdf):'embed='+encodeURIComponent(embed))+'&title='+encodeURIComponent(b.title);let action='';if(pdf||embed)action=`<a class="button button-small" href="${esc(reader)}">Sayt ichida o‘qish →</a>`;else action='<span class="muted">O‘qish havolasi mavjud emas</span>';const cover=b.cover?`<img class="cover" src="${esc(b.cover)}" alt="Muqova" loading="lazy">`:`<div class="cover placeholder"><span>✧</span><b>${esc(b.title.slice(0,40))}</b></div>`;return `<article class="bookcard"><div class="book-cover-link">${cover}</div><div class="bookbody"><span class="subject">${esc(b.source)}</span><h3>${esc(b.title)}</h3><p class="author">${esc(b.author)}</p><div class="actions">${action}</div></div></article>`;}).join('');
  }catch(err){status.textContent='Qidiruv vaqtida xatolik: '+err.message;grid.innerHTML='<div class="empty"><h3>Qidiruv amalga oshmadi</h3><p>Internet aloqasini tekshirib, qayta urinib ko‘ring.</p></div>';}
 };
 form.addEventListener('submit',runSearch);
 const existingQuery=new URLSearchParams(location.search).get('q');if(existingQuery){input.value=existingQuery;runSearch();}
})();
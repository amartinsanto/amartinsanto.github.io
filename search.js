
const normalize=s=>s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('es');
const source=JSON.parse(document.getElementById('search-data').textContent);
const texts=Object.fromEntries(Object.entries(source).map(([k,v])=>[k,normalize(v)]));
const cards=[...document.querySelectorAll('.card')];
const input=document.getElementById('search'),category=document.getElementById('category');
document.getElementById('filters').hidden=false;
function filter(){const words=normalize(input.value).trim().split(/\s+/).filter(Boolean);let count=0;for(const card of cards){const show=(!category.value||card.dataset.category===category.value)&&words.every(w=>texts[card.dataset.slug].includes(w));card.hidden=!show;if(show)count++;}document.getElementById('count').textContent=count+' '+(count===1?'entrada':'entradas');document.getElementById('empty').hidden=count!==0;}
input.addEventListener('input',filter);category.addEventListener('change',filter);

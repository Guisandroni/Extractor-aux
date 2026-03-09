# Auction Website Patterns & Platforms

Analysis of discovered auctioneer websites to identify common platforms and technology providers.

## Top Platforms Identified
- **Unknown / Custom**: 35 sites
- **Unreachable**: 7 sites
- **Caixa**: 3 sites
- **BomValor Tech**: 2 sites
- **Superbid Technology**: 2 sites
- **Lance Judicial**: 1 sites

## Detailed Analysis (Sample)
| Website | Detected Platform/Keywords |
|---|---|| https://www.ckleiloes.com.br | Unknown / Custom |
| https://www.mariafixerleiloes.com.br | Unknown / Custom |
| https://www.leiloesjvfarias.com.br | Unreachable |
| https://www.elydaluzramos.com.br | Unknown / Custom |
| https://www.albuquerquelins.com.br/ | Caixa |
| https://marianalangleiloes.com.br/ | Unreachable |
| https://www.leilaopernambuco.com.br/ | Unknown / Custom |
| http://www.julileiloes.com.br | Unknown / Custom |
| https://www.leiloeirojudicial.lel.br | Unknown / Custom |
| https://www.britoleiloes.com.br | Unreachable |
| https://www.leiloeirosdebrasilia.com.br | Unknown / Custom |
| https://www.mlleiloes.com.br | Unknown / Custom |
| https://www.topleiloes.com.br | Unknown / Custom |
| http://www.mpleilao.com.br | Unknown / Custom |
| https://www.joaoluizleiloes.com.br/ | Unknown / Custom |
| https://www.ajleiloes.com.br | BomValor Tech |
| http://www.leiloespb.com.br | Unknown / Custom |
| http://www.zagoleiloes.com.br | Unknown / Custom |
| https://www.cesarmoresco.com.br | Unreachable |
| https://www.albertomacedoleiloes.com.br | Superbid Technology |
| https://www.lancejudicial.com.br/ | Lance Judicial |
| https://www.lkleiloes.com.br | Unknown / Custom |
| https://eduardoleiloeiro.com.br | Unknown / Custom |
| https://www.leiloesuberlandia.com.br | Unknown / Custom |
| https://www.ineuleiloes.com.br/ | Unreachable |
| https://www.leilaobutia.com.br | Unknown / Custom |
| https://www.backleiloes.com.br | Unknown / Custom |
| https://www.3torresleiloes.com.br | Unknown / Custom |
| https://www.leiloesceruli.com.br | Caixa |
| http://www.diariooficial.rs.gov.br/materia?id=714813 | Unreachable |
| https://www.topoleiloes.com.br | Unknown / Custom |
| http://www.diariooficial.rs.gov.br/materia?id=252888 | Unknown / Custom |
| https://www.moacira.lel.br | Unknown / Custom |
| https://www.utzigleiloes.com.br | Unknown / Custom |
| https://www.diariooficial.rs.gov.br/materia?id=713070 | Unknown / Custom |
| https://www.buaizleiloes.com.br/ | Unknown / Custom |
| https://www.gtleiloes.com.br | Unknown / Custom |
| http://www.diariooficial.rs.gov.br/materia?id=279111 | Unknown / Custom |
| https://www.arremataronline.com.br/ | BomValor Tech |
| https://www.baronleiloes.com.br | Unknown / Custom |
| https://www.bastonleiloes.com.br/ | Unknown / Custom |
| https://www.gomesleiloes.com.br/ | Unreachable |
| http://www.diariooficial.rs.gov.br/materia?id=557037 | Unknown / Custom |
| https://www.hoppeleiloes.com.br/ | Superbid Technology |
| http://www.diariooficial.rs.gov.br/materia?id=849977 | Unknown / Custom |
| http://www.turanileiloes.com.br | Unknown / Custom |
| https://www.casadoleilao.com | Caixa |
| https://www.fauthleiloes.com.br | Unknown / Custom |
| https://www.patiorochaleiloes.com.br/ | Unknown / Custom |
| https://www.macedoleiloes.com.br | Unknown / Custom |

## Extraction Strategy Recommendations
Based on the findings, here are strategies for extracting auction data:

1. **Superbid / BomValor / Lance Judicial:** These appear to be major aggregators or tech providers. Writing specific spiders for their DOM structure will yield high returns as many sites use their backend.
2. **Custom Sites:** Many auctioneers have custom WordPress or PHP sites. A generic scraper looking for keywords like 'Lote', 'Lance', 'Edital', 'Próximos Leilões' is needed.
3. **Common Data Points:** Almost all sites list:
   - `Status` (Aberto, Encerrado, Breve)
   - `Data` (1ª Praça, 2ª Praça)
   - `Valor` (Avaliação, Lance Mínimo)
   - `Foto` (Thumbnail of the lot)

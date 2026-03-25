const fs = require('fs');

// Load the games.json file
const gamesPath = '../data/games.json';
const data = JSON.parse(fs.readFileSync(gamesPath, 'utf8'));

let testedCount = 0;
let brokenCount = 0;
let modifiedGames = [];

async function testUrl(url) {
  try {
    const response = await fetch(url, { 
      method: 'HEAD',
      timeout: 5000,
      headers: {
        'User-Agent': 'Mozilla/5.0'
      }
    });
    return response.status;
  } catch (error) {
    return null; // Error during request
  }
}

async function processGames() {
  for (let i = 0; i < data.games.length; i++) {
    const game = data.games[i];
    
    if (game.url && game.url.startsWith('https://archipelago.gg/games/')) {
      const status = await testUrl(game.url);
      testedCount++;
      
      console.log(`[${i + 1}/${data.games.length}] ${game.name} (${game.id}): ${status || 'ERROR'}`);
      
      if (status === 404) {
        console.log(`  ❌ 404 Not Found - Removing URL`);
        modifiedGames.push(game.id);
        brokenCount++;
        delete game.url;
      } else if (status === null) {
        console.log(`  ⚠️  Could not test (timeout/error)`);
      } else if (status === 200) {
        console.log(`  ✅ OK`);
      } else {
        console.log(`  ⚠️  Status ${status}`);
      }
      
      // Add delay to avoid rate limiting
      await new Promise(resolve => setTimeout(resolve, 200));
    }
  }
  
  // Write the modified data back
  fs.writeFileSync(gamesPath, JSON.stringify(data, null, 2) + '\n', 'utf8');
  
  console.log(`\n✅ Testing complete!`);
  console.log(`   Tested: ${testedCount} URLs from archipelago.gg/games/`);
  console.log(`   Removed: ${brokenCount} broken URLs`);
  if (modifiedGames.length > 0) {
    console.log(`   Modified games: ${modifiedGames.join(', ')}`);
  }
}

processGames().catch(console.error);

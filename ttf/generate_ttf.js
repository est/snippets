const fs = require('fs');

// Utility functions for TTF construction
function u16(v) { return [v >> 8, v & 255]; }
function u32(v) { return [v >> 24, (v >> 16) & 255, (v >> 8) & 255, v & 255]; }
function bytesToString(bytes) { return String.fromCharCode(...bytes); }
function stringToBytes(str) { return Array.from(str).map(c => c.charCodeAt(0)); }
function pad4(arr) { while (arr.length % 4) arr.push(0); return arr; }

function checksum(data) {
    let sum = 0;
    for (let i = 0; i < data.length; i += 4) {
        sum = (sum + (
            ((data[i] || 0) << 24) |
            ((data[i + 1] || 0) << 16) |
            ((data[i + 2] || 0) << 8) |
            (data[i + 3] || 0)
        )) >>> 0;
    }
    return sum;
}

// Create minimal valid TTF with single glyph
function createZeroWidthTTF() {
    const tables = [];

    // 1. glyf - single empty glyph
    const glyfTable = [
        0, 0,    // numberOfContours (0 for empty glyph)
        0, 0,    // xMin
        0, 0,    // yMin
        0, 0,    // xMax
        0, 0     // yMax
    ];
    tables.push({ tag: "glyf", data: pad4(glyfTable), checksum: 0 });

    // 2. loca - glyph location table
    tables.push({ tag: "loca", data: pad4([0, 0]), checksum: 0 });

    // 3. hmtx - horizontal metrics
    tables.push({ tag: "hmtx", data: pad4([0, 0, 0, 0]), checksum: 0 });

    // 4. maxp - maximum profile
    tables.push({ tag: "maxp", data: pad4([
        ...u32(0x00010000),    // version 1.0
        ...u16(1),             // numGlyphs
        ...u16(0), ...u16(0),  // maxPoints, maxContours
        ...u16(0), ...u16(0),  // maxCompositePoints, maxCompositeContours
        ...u16(0), ...u16(0),  // maxZones, maxTwilightPoints
        ...u16(0), ...u16(0),  // maxStorage, maxFunctionDefs
        ...u16(0), ...u16(0),  // maxInstructionDefs, maxStackElements
        ...u16(0), ...u16(0),  // maxSizeOfInstructions, maxComponentElements
        ...u16(0)              // maxComponentDepth
    ]), checksum: 0 });

    // 5. head - font header (36 bytes)
    tables.push({ tag: "head", data: pad4([
        ...u32(0x00010000),    // version 1.0
        ...u32(0),             // checkSumAdjustment (will be calculated)
        ...u32(0x5F0F3CF5),    // magicNumber
        ...u16(0),             // flags
        ...u16(1000),          // unitsPerEm
        ...u32(0), ...u32(0),  // created, modified (placeholder)
        ...u16(-200), ...u16(-200), // xMin, yMin
        ...u16(1200), ...u16(1200), // xMax, yMax
        ...u16(0), ...u16(10), // macStyle, lowestRecPPEM
        ...u16(2), ...u16(0), ...u16(0) // fontDirectionHint, indexToLocFormat, glyphDataFormat
    ]), checksum: 0 });

    // 6. hhea - horizontal header (36 bytes)
    tables.push({ tag: "hhea", data: pad4([
        ...u32(0x00010000),    // version 1.0
        ...u16(-200), ...u16(-200), // ascent, descent
        ...u16(0),             // lineGap
        ...u16(1000),          // advanceWidthMax
        ...u16(-200), ...u16(-200), // minLeftSideBearing, minRightSideBearing
        ...u16(0),             // xMaxExtent
        ...u16(1),             // caretSlopeRise
        ...u16(0),             // caretSlopeRun
        ...u32(0),             // caretOffset
        ...u16(0), ...u16(1)   // metricDataFormat, numberOfHMetrics
    ]), checksum: 0 });

    // 7. cmap - character to glyph mapping (format 4, ~44 bytes)
    tables.push({ tag: "cmap", data: pad4([
        0, 0, 0, 1,            // version, number of tables
        0, 3, 0, 1, 0, 0, 0, 12, // platformID, platformSpecificID, offset
        ...u16(4), ...u16(44), ...u16(0), // format, length, language
        ...u16(1), ...u16(8), ...u16(0), ...u16(0), // nGroups, searchRange, entrySelector, rangeShift
        ...u16(0x2603), ...u16(0x2603), ...u16(0) // startCharCode, endCharCode, glyphID
    ]), checksum: 0 });

    // 8. name - font naming (6 bytes)
    tables.push({ tag: "name", data: pad4([0, 0, 0, 0, 0, 0]), checksum: 0 });

    // 9. post - PostScript info (32 bytes)
    tables.push({ tag: "post", data: pad4([
        ...u32(0x00010000), // version 1.0
        ...u32(0),         // italicAngle
        ...u16(0), ...u16(0), // underlinePosition, underlineThickness
        ...u32(0),         // isFixedPitch
        ...u32(0), ...u32(0), // minMemType42, maxMemType42
        ...u32(0), ...u32(0)  // minMemType1, maxMemType1
    ]), checksum: 0 });

    // 10. OS/2 table (78 bytes minimum)
    tables.push({ tag: "OS/2", data: pad4([
        ...u16(0x0004), 0, 0,
        ...u16(1000), ...u16(5), ...u16(0),
        ...u16(1000), ...u16(1000), ...u16(0), ...u16(0),
        ...u16(1200), ...u16(1200), ...u16(0), ...u16(0),
        ...u16(200), ...u16(0), ...u16(0),
        0, 0, 0, 0, 0, 0, 0, 0,
        ...u32(0), ...u32(0), ...u32(0), ...u32(0),
        ...u16(0x0409), ...u16(0),
        ...u16(65535), ...u16(0),
        ...u16(0), ...u16(0), ...u16(0),
        ...u16(1200), ...u16(200),
        ...new Array(78 - 60).fill(0) // 补全到最小长度
    ].flat()), checksum: 0 });

    // Sort tables alphabetically by tag
    const sortedTables = [...tables].sort((a, b) => a.tag.localeCompare(b.tag));

    // Calculate offsets and lengths
    let offset = 12 + sortedTables.length * 16;
    sortedTables.forEach(t => {
        t.offset = offset;
        t.length = t.data.length;
        t.checksum = checksum(t.data);
        offset += t.length;
    });

    // Calculate checkSumAdjustment
    const headTable = sortedTables.find(t => t.tag === "head");
    if (headTable) {
        let totalChecksum = 0;
        sortedTables.forEach(t => {
            totalChecksum += t.checksum;
            totalChecksum &= 0xffffffff;
        });
        const checkSumAdjustment = (0xB1B0AFBA - totalChecksum) & 0xffffffff;
        headTable.data.splice(4, 4, ...u32(checkSumAdjustment));
        headTable.checksum = checksum(headTable.data);
    }

    // Build the TTF file
    const out = [];
    out.push(...u32(0x00010000));

    // Calculate search parameters
    const numTables = sortedTables.length;
    let powerOf2 = 0;
    while ((1 << (powerOf2 + 1)) <= numTables) powerOf2++;
    const searchRange = (1 << powerOf2) * 16;
    const entrySelector = powerOf2;
    const rangeShift = numTables * 16 - searchRange;

    out.push(...u16(numTables));
    out.push(...u16(searchRange));
    out.push(...u16(entrySelector));
    out.push(...u16(rangeShift));

    // Write table records
    sortedTables.forEach(t => {
        const tagBytes = [];
        for (let i = 0; i < 4; i++) {
            tagBytes.push(t.tag.charCodeAt(i) || 0);
        }
        out.push(...tagBytes);
        out.push(...u32(t.checksum), ...u32(t.offset), ...u32(t.length));
    });

    // Write table data
    sortedTables.forEach(t => out.push(...t.data));

    return new Uint8Array(out);
}

// Generate and save the TTF file
const ttfData = createZeroWidthTTF();
fs.writeFileSync('generated_font.ttf', Buffer.from(ttfData));
console.log('TTF file generated successfully: generated_font.ttf');
